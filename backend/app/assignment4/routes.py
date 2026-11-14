"""Thin local controls and complete-state WebSocket transport. No source starts on connect."""
import asyncio
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Request, WebSocket, WebSocketDisconnect
from .dashboard_models import StartBody, HistoryBody

from .dashboard import ControlError

router = APIRouter(prefix="/api/assignment4")
ORIGINS = {"http://127.0.0.1:5174", "http://localhost:5174",
           "http://127.0.0.1:8001", "http://localhost:8001"}


def local_control(request: Request):
    if request.headers.get("origin") not in ORIGINS | {None}:
        raise HTTPException(403, "Local dashboard origin required")
    return request.app.state.dashboard


@router.get("/health")
def health(request: Request) -> dict:
    return {"status": "ok", "application": "assignment4", "stage": "integrated",
            "feed_status": request.app.state.dashboard.control["feed"],
            "live_task_running": request.app.state.dashboard.control["running"]}


@router.get("/candles")
def candles(request: Request) -> dict:
    return request.app.state.market_service.snapshot()


@router.get("/receipts")
def receipts(request: Request, after: Annotated[int, Query(ge=0)] = 0,
             limit: Annotated[int, Query(ge=1, le=500)] = 100) -> dict:
    rows = request.app.state.market_service.receipts(after, limit)
    return {"receipts": rows, "next_after": rows[-1]["receipt_seq"] if rows else after}


@router.get("/replay")
def replay(request: Request, through: Annotated[int | None, Query(ge=0)] = None) -> dict:
    return request.app.state.market_service.replay(through)


@router.get("/dashboard")
async def dashboard_state(request: Request) -> dict:
    return await request.app.state.dashboard.snapshot()


@router.post("/live/start")
async def start_live(body: StartBody, request: Request) -> dict:
    dashboard = local_control(request)
    try:
        await dashboard.start(body.symbols, body.seconds)
    except ControlError as exc:
        raise HTTPException(409, str(exc)) from None
    return {"started": True, "duration_seconds": body.seconds}


@router.post("/live/stop")
async def stop_live(request: Request) -> dict:
    await local_control(request).stop()
    return {"stopped": True}


@router.post("/interval/fetch")
async def fetch_interval(body: HistoryBody, request: Request) -> dict:
    try:
        return await local_control(request).fetch_history(body.symbol)
    except ControlError as exc:
        raise HTTPException(409, str(exc)) from None


@router.post("/demo/unavailable")
async def unavailable_demo(request: Request) -> dict:
    await local_control(request).simulate_unavailable()
    return {"simulated": True, "source_requests": 0}


@router.websocket("/ws")
async def socket(websocket: WebSocket) -> None:
    if websocket.headers.get("origin") not in ORIGINS | {None}:
        await websocket.close(code=1008)
        return
    await websocket.accept()
    dashboard = websocket.app.state.dashboard
    queue = None
    receiver = queued = None
    mode, through, replay_end = "live", None, None
    request_id = 0
    try:
        hello = await asyncio.wait_for(websocket.receive_json(), timeout=5)
        if hello.get("type") != "hello":
            await websocket.close(code=1008)
            return
        queue, initial = await dashboard.subscribe()
        mode = "replay" if hello.get("mode") == "replay" else "live"
        request_id = int(hello.get("request_id", 0))
        if mode == "replay":
            replay_end = min(initial["payload"]["max_cursor"],
                             max(0, int(hello.get("end", initial["payload"]["max_cursor"]))))
            through = min(replay_end, max(0, int(hello.get("cursor", 0))))
            initial = await dashboard.snapshot(mode, through)
            initial["payload"]["max_cursor"] = replay_end
        initial["request_id"] = request_id
        await websocket.send_json(initial)
        receiver = asyncio.create_task(websocket.receive_json())
        queued = asyncio.create_task(queue.get())
        while True:
            done, _ = await asyncio.wait({receiver, queued}, timeout=5,
                                         return_when=asyncio.FIRST_COMPLETED)
            kind = "heartbeat"
            if receiver in done:
                command = receiver.result()
                receiver = asyncio.create_task(websocket.receive_json())
                request_id = int(command.get("request_id", request_id))
                if command.get("type") == "replay":
                    if mode != "replay":
                        current = await dashboard.snapshot()
                        replay_end = current["payload"]["max_cursor"]
                    mode = "replay"
                    through = min(replay_end, max(0, int(command.get("cursor", 0))))
                elif command.get("type") == "live":
                    mode, through, replay_end = "live", None, None
                else:
                    await websocket.close(code=1008)
                    return
                kind = "snapshot"
            if queued in done:
                signal = queued.result()
                queued = asyncio.create_task(queue.get())
                if kind == "heartbeat" and mode == "live":
                    kind = "resync" if signal == "resync" else "update"
                elif kind == "heartbeat" and mode == "replay":
                    continue  # Live publications never advance a frozen replay.
            frame = await dashboard.snapshot(mode, through)
            frame["message_type"], frame["request_id"] = kind, request_id
            if mode == "replay":
                frame["payload"]["max_cursor"] = replay_end
            await websocket.send_json(frame)
    except (WebSocketDisconnect, TimeoutError, ValueError, TypeError, KeyError, asyncio.CancelledError):
        pass
    finally:
        for task in (receiver, queued):
            if task:
                task.cancel()
        try:
            await asyncio.gather(*(t for t in (receiver, queued) if t), return_exceptions=True)
        except asyncio.CancelledError:
            pass
        if queue:
            dashboard.clients.discard(queue)

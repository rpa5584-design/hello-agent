# Historical 55-second video handoff plan

**Current status — November 14, 2026:** the author has retained the original `evidence/assignment4.1-demo.mp4`, measured at **81.0 seconds**, unchanged. It exceeds the required 30–60 seconds; no trim, speed change, replacement or re-recording is authorized. The plan below predates that retained recording and is historical, not an instruction to produce a new video. Public publication/accessibility is unverified; see [submission report](submission/report.md).

Implementation commit:3bb33315f23e9697ede34218040cdeea27696ecc. This plan uses committed ACTUAL live screenshots plus the no-network recorded-data dashboard. Do not start another Yahoo session. No automated screen/video recorder is exposed by the connected browser tools; tool discovery found none and ffmpeg was not available on PATH. Screenshots are not a video. Windows Snipping Tool is available for manual region recording; recording/accessibility remains unchecked.

## Exact next manual step

1. From backend/ in the verified checkout, launch a fresh offline DB with the README command: ./.venv/Scripts/python.exe -m app.assignment4.run_dashboard --database data/video-demo.sqlite3 --offline --recording ../docs/assignment4/part4.1/evidence/live-refresh-recording.json . If reusing that imported DB, omit --recording. Start frontend on5174 using README, then open /assignment4.html. Never select the live launcher for this recording.
2. Open evidence/live-refresh-initial.jpg and live-refresh-automatic.jpg in image tabs; these are earlier actual browser captures, not a present feed. Keep unrelated/personal windows outside the capture region.
3. Press Win+Shift+R, choose only the dashboard/image region in Snipping Tool, and start a55-second recording. Narrate or add explicit titles as below. Do not label recorded evidence as a currently streaming session.

| Seconds | Actual screen/action | Suggested wording |
| --- | --- | --- |
|0-8 | Offline dashboard title, OFFLINE RECORDED DATA banner, source/status/ages | "This is saved Yahoo evidence in a network-disabled localhost Vue/FastAPI/SQLite dashboard." |
|8-20 | Show the ACTUAL initial and automatic-refresh screenshots captured05:18/05:19UTC, plus their source/retrieval labels | "One actual83-second BTC session received12 stream observations. Two automatic interval retrievals arrived60seconds apart." |
|20-30 | Return offline dashboard Yahoo interval mode, visible candle AND volume panes and latest OHLCV record | "OHLC and volume come from the same interval record. These valid bar values stayed unchanged across the two fetches; crypto units are provider-reported." |
|30-38 | Click Stream-observed candles, show volume unknown | "Streaming prices form a separate partial candle product. We do not attach historical volume to it." |
|38-46 | Replay saved receipts, Play or move saved cursor | "Replay uses original receipt order and immutable versions, without future revisions leaking backwards." |
|46-55 | Live view remains offline-labelled; Simulate unavailable; saved chart retained | "This unavailable condition is explicitly simulated. Data commits before WebSocket publication, and Stop ended all scheduled requests." |

4. Stop recording at45-60seconds and save an actual MP4. Play it end-to-end: verify duration/readable chart/status labels, accurate captions/audio and no private material. If a source/volume change is not visible, do not narrate one.
5. Upload only after reviewing the actual video, then test its viewing URL signed out/private. Put the accessible video URL, repository URL and exact submitted commit into the separate Assignment4 report. No recording, upload, public link or accessibility is asserted here. Root report.md remains Assignment3 and untouched.

If the actual live screenshot text is too small, enlarge its viewer before recording; do not redraw or fabricate it. A video of saved data must retain the recorded/offline/replay distinctions. Instructor acceptance of streamed-price plus polled matching OHLCV is unconfirmed. Full verification links provide details the short video cannot prove.

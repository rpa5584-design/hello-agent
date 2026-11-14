"""Independent dashboard; initialization/teardown only, no automatic source connection."""
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from . import database
from .dashboard import Dashboard
from .routes import router
from .services import MarketService


def create_app(database_path: Path | None = None, *, adapter_factory=None,
               history_fetcher=None, max_attempts: int = 2, offline: bool = False) -> FastAPI:
    path = Path(database_path) if database_path is not None else database.DATABASE_PATH

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        database.initialize(path)
        options = {"history_fetcher": history_fetcher, "max_attempts": max_attempts, "offline": offline}
        if adapter_factory is not None:
            options["adapter_factory"] = adapter_factory
        application.state.dashboard = Dashboard(path, **options)
        try:
            yield
        finally:
            await application.state.dashboard.close()

    application = FastAPI(title="Assignment 4 Market Dashboard", lifespan=lifespan)
    application.state.database_path = path
    application.state.market_service = MarketService(path)
    application.include_router(router)
    return application

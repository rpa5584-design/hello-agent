"""Assignment 3 application factory, separate from RoomTour startup."""
from contextlib import asynccontextmanager
from pathlib import Path
import sqlite3
from collections.abc import AsyncIterator
from fastapi import FastAPI
from . import database
from .routes import router


def create_app(database_path: Path | None = None) -> FastAPI:
    path = database_path if database_path is not None else database.DATABASE_PATH

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        try:
            database.initialize(path)
        except (sqlite3.Error, OSError):
            # Static UI and health remain usable; storage requests report errors.
            pass
        yield

    application = FastAPI(title="Assignment 3 Skills Prototype API", lifespan=lifespan)
    application.state.database_path = path
    application.include_router(router)
    return application

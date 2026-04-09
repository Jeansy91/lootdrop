import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from .config import settings
from .database import create_db_and_tables, migrate
from .scheduler import scheduler, start_scheduler
from .routes import admin, public, subscribe

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    migrate()
    await start_scheduler()
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(title="Lootdrop", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    max_age=60 * 60 * 8,  # 8 Stunden
)

app.include_router(public.router)
app.include_router(subscribe.router)
app.include_router(admin.router)

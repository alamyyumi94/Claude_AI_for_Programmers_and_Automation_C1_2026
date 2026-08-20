from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.api.router import api_router
from app.config import get_settings
from app.database import( connect_to_database, close_database)

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Open required resources (e.g., database connections) at startup
    await connect_to_database()

    try:
        yield  # Control is transferred to the application
    finally:
        # Clean up resources (e.g., close database connections) at shutdown
        await close_database()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # open any required resources
    await connect_to_database()
    try:
        yield
    finally:
        await close_database_connection()


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

app.include_router(api_router)

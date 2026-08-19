from fastapi import FastAPI

from app.api.routes.router import api_router
from app.config import get_settings


settings = get_settings()

app = FastAPI(title=settings.app_name, version="0.1.0")

app.include_router(api_router)

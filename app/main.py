from fastapi import FastAPI

from app.api.routes.router import api_router

app = FastAPI(title="Support Ops Ai", version="0.1.0")

app.include_router(api_router)

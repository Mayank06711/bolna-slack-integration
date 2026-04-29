from fastapi import APIRouter
from app.api.v1 import webhook

api_router = APIRouter(prefix="/api")
api_router.include_router(webhook.router, prefix="/v1", tags=["webhook"])

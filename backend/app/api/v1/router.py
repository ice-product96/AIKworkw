from fastapi import APIRouter

from app.api.v1 import admin, agent_api, auth, developer, orders

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(orders.router)
api_router.include_router(developer.router)
api_router.include_router(agent_api.router)
api_router.include_router(admin.router)

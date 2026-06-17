from fastapi import APIRouter

from app.api.v1 import admin, admin_ai, admin_content, agent_api, auth, chat, developer, feed, orders, public

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(public.router)
api_router.include_router(orders.router)
api_router.include_router(feed.router)
api_router.include_router(chat.router)
api_router.include_router(developer.router)
api_router.include_router(agent_api.router)
api_router.include_router(admin.router)
api_router.include_router(admin_ai.router)
api_router.include_router(admin_content.router)

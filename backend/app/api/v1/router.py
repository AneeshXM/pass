"""API v1 router combining all endpoints."""
from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, vaults, credentials, tags, groups, audit, mfa

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(vaults.router)
api_router.include_router(credentials.router)
api_router.include_router(tags.router)
api_router.include_router(groups.router)
api_router.include_router(audit.router)
api_router.include_router(mfa.router)
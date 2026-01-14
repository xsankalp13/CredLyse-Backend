"""
API v1 Router

Aggregates all v1 endpoint routers.
"""

from fastapi import APIRouter

router = APIRouter()

# Import and include routers here as they are created
# Example:
# from app.api.v1.endpoints import users, courses, progress
# router.include_router(users.router, prefix="/users", tags=["users"])
# router.include_router(courses.router, prefix="/courses", tags=["courses"])
# router.include_router(progress.router, prefix="/progress", tags=["progress"])

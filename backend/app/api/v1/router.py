from fastapi import APIRouter

from app.api.v1.routes.submission import router as submission_router

router = APIRouter()
router.include_router(submission_router, prefix="/submissions", tags=["submissions"])

from fastapi import APIRouter

from app.api.v1.routes.problem import router as problem_router
from app.api.v1.routes.queue import router as queue_router
from app.api.v1.routes.run import router as run_router
from app.api.v1.routes.submission import router as submission_router

router = APIRouter()
router.include_router(problem_router, prefix="/problems", tags=["problems"])
router.include_router(queue_router, prefix="/queue", tags=["queue"])
router.include_router(run_router, prefix="/runs", tags=["runs"])
router.include_router(submission_router, prefix="/submissions", tags=["submissions"])

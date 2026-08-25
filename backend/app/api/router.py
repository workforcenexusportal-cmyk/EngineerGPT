"""Aggregate the v1 API surface from auth + every platform module."""

from __future__ import annotations

from fastapi import APIRouter

from app.api import auth
from app.modules.design_review.router import router as design_review_router
from app.modules.failure_analysis.router import router as failure_router
from app.modules.knowledge_hub.router import router as knowledge_router
from app.modules.meeting_prep.router import router as meeting_router
from app.modules.requirements_intel.router import router as requirements_router
from app.modules.test_report.router import router as test_report_router

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(test_report_router)
api_router.include_router(knowledge_router)
api_router.include_router(failure_router)
api_router.include_router(requirements_router)
api_router.include_router(meeting_router)
api_router.include_router(design_review_router)

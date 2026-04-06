"""
Interview Service — public API shim.

Re-exports all public functions from the split service modules
so existing imports continue to work without changes.
"""
from app.services.interview_history_service import (
    get_improvement_history,
    get_session_result,
    get_user_sessions,
)
from app.services.interview_session_service import (
    get_practice_question,
    get_session_feedback,
    ingest_keywords_and_generate,
    start_interview_session,
    submit_batch_answer,
    submit_practice_answer,
)

__all__ = [
    "get_improvement_history",
    "get_session_result",
    "get_user_sessions",
    "get_practice_question",
    "get_session_feedback",
    "ingest_keywords_and_generate",
    "start_interview_session",
    "submit_batch_answer",
    "submit_practice_answer",
]
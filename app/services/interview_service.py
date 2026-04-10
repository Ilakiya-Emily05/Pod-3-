"""
interview_service.py - compatibility shim.
Delegates to the real service modules.
"""

from app.services.interview_practice_service import (
    get_practice_question,
    ingest_keywords_and_generate,
    submit_practice_answer,
)
from app.services.interview_progress_service import (
    get_improvement_history,
    get_session_result,
    get_user_sessions,
)

__all__ = [
    "get_improvement_history",
    "get_practice_question",
    "get_session_result",
    "get_user_sessions",
    "ingest_keywords_and_generate",
    "submit_practice_answer",
]

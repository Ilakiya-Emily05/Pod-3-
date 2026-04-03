_models_registered = False


def register_models() -> None:
    """Register all models with SQLAlchemy's MetaData. Safe to call multiple times."""
    global _models_registered

    if _models_registered:
        return

    from app.models.progress import UserProgress

    from app.models.user import (
        User,
        AdminUser,
        UserProfile,
    )

    from app.models.interview_system import (
        DifficultyLevel,
        KeySkill,
        Question,
        InterviewSession,
        UserResponse,
    )

    # ── New analytics models (Sprint 2 Task 1) ────────────────────
    from app.models.analytics_models import (
        SessionAnalytics,
        UserMilestone,
        SkillScoreHistory,
    )

    from app.models.grammar import (
        GrammarAssessment,
        GrammarQuestion,
        GrammarQuestionOption,
        GrammarAttempt,
        GrammarAttemptAnswer,
    )

    from app.models.listening import (
        ListeningAssessment,
        ListeningQuestion,
        ListeningQuestionOption,
        ListeningAttempt,
        ListeningAttemptAnswer,
    )

    from app.models.reading import (
        ReadingAssessment,
        ReadingQuestion,
        ReadingQuestionOption,
        ReadingAttempt,
        ReadingAttemptAnswer,
    )

    from app.models.assessment_status import (
        AttemptStatus,
        CEFRLevel,
    )

    from app.models.resume import Resume

    _models_registered = True
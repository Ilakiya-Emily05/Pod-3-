from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.assessment_session import (
    AssessmentSession,
    AssessmentSection,
    AssessmentSessionStatus,
    AssessmentSessionType,
)


# ---------- Helper: section flow ----------
PRE_TEST_FLOW = [
    AssessmentSection.A_READING,
    AssessmentSection.B_SPEAKING,
    AssessmentSection.C_GRAMMAR,
    AssessmentSection.D_LISTENING,
]

POST_TEST_FLOW = PRE_TEST_FLOW + [AssessmentSection.E_WRITING]


def get_flow(session_type: AssessmentSessionType):
    return POST_TEST_FLOW if session_type == AssessmentSessionType.POST_TEST else PRE_TEST_FLOW


# ---------- Service ----------
class AssessmentSessionService:

    @staticmethod
    async def create_session(
        db: AsyncSession,
        user_id: uuid.UUID,
        session_type: AssessmentSessionType,
    ) -> AssessmentSession:
        session = AssessmentSession(
            user_id=user_id,
            session_type=session_type,
            status=AssessmentSessionStatus.IN_PROGRESS,
            current_section=AssessmentSection.A_READING,
        )

        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session

    @staticmethod
    async def get_session(
        db: AsyncSession,
        session_id: uuid.UUID,
    ) -> AssessmentSession:
        result = await db.execute(
            select(AssessmentSession).where(AssessmentSession.id == session_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            raise ValueError("Session not found")

        return session

    @staticmethod
    async def submit_section(
        db: AsyncSession,
        session_id: uuid.UUID,
        section: AssessmentSection,
    ) -> AssessmentSession:
        session = await AssessmentSessionService.get_session(db, session_id)

        if session.status == AssessmentSessionStatus.COMPLETED:
            raise ValueError("Session already completed")

        # enforce order
        if session.current_section != section:
            raise ValueError("Invalid section order")

        flow = get_flow(session.session_type)
        current_index = flow.index(section)

        # move to next section or complete
        if current_index < len(flow) - 1:
            session.current_section = flow[current_index + 1]
        else:
            session.status = AssessmentSessionStatus.COMPLETED
            session.completed_at = datetime.now(UTC)

            # placeholder aggregation (replace later)
            session.composite_cefr_result = "B1"

        await db.commit()
        await db.refresh(session)
        return session

    @staticmethod
    async def get_result(
        db: AsyncSession,
        session_id: uuid.UUID,
    ) -> AssessmentSession:
        session = await AssessmentSessionService.get_session(db, session_id)

        if session.status != AssessmentSessionStatus.COMPLETED:
            raise ValueError("Session not completed")

        return session
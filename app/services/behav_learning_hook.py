from datetime import datetime
from typing import Any, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.behav_assessment_model import BehavProfile
from app.schemas.behav_assessment_schemas import (
    BehavioralCompleteResponse,
    BehavioralProfileResponse,
    ModuleRecommendation,
    TraitScore,
)
from app.services import behav_assessment_service


class BehavioralLearningService:

    TRAIT_THRESHOLD = 50  # Below this suggests development need

    MODULE_MAPPING = {
        "honesty_humility": {
            "name": "Honesty-Humility",
            "low_modules": [
                {"name": "business_ethics", "reason": "Focus on ethical decision-making and professional integrity."},
                {"name": "client_trust", "reason": "Learn strategies for building and maintaining long-term client trust."}
            ],
        },
        "emotionality": {
            "name": "Emotionality",
            "high_modules": [
                {"name": "stress_management", "reason": "Techniques for maintaining composure in high-pressure environments."},
                {"name": "emotional_regulation", "reason": "Developing resilience and emotional stability during setbacks."}
            ],
            "low_modules": [
                {"name": "empathy_training", "reason": "Enhancing social sensitivity and emotional connection with others."},
                {"name": "active_listening", "reason": "Improving response accuracy through focused auditory engagement."}
            ],
        },
        "extraversion": {
            "name": "Extraversion",
            "low_modules": [
                {"name": "networking_skills", "reason": "Building confidence and strategy for effective professional networking."},
                {"name": "gd_preparation", "reason": "Improving group discussion performance and social leadership."},
                {"name": "public_speaking", "reason": "Developing authoritative and engaging presentation skills."}
            ],
        },
        "agreeableness": {
            "name": "Agreeableness",
            "low_modules": [
                {"name": "conflict_resolution", "reason": "Strategies for managing disagreements with diplomacy and tact."},
                {"name": "team_collaboration", "reason": "Fostering a supportive and harmonious team environment."}
            ],
        },
        "conscientiousness": {
            "name": "Conscientiousness",
            "low_modules": [
                {"name": "time_management", "reason": "Mastering task prioritization and efficient scheduling."},
                {"name": "professional_etiquette", "reason": "Understanding workplace norms and professional reliability."},
                {"name": "goal_setting", "reason": "Learning systematic approaches to achieving long-term objectives."}
            ],
        },
        "openness": {
            "name": "Openness",
            "low_modules": [
                {"name": "growth_mindset", "reason": "Cultivating openness to feedback and continuous learning."},
                {"name": "feedback_reception", "reason": "Developing a constructive approach to receiving and utilizing critique."},
                {"name": "creative_thinking", "reason": "Techniques for innovative problem-solving and brainstorming."}
            ],
        },
    }

    async def get_session_scores(self, db: AsyncSession, session_id: UUID) -> dict[str, Any]:
        # 1. Fetch scores from session
        result = await behav_assessment_service.calculate_result(db, session_id)
        return result

    def calculate_hexaco_profile(self, scores_result: dict[str, Any]) -> dict[str, float]:
        # 2. Calculate HEXACO profile
        return scores_result["hexaco_scores"]


    def generate_recommendations(self, profile: dict[str, float]) -> List[ModuleRecommendation]:
        # 4. Map to recommended modules using Comparative and Absolute logic
        recommendations = []
        
        # Identify comparative points (lowest score in profile)
        # Avoid identifying a "low" if everything is a perfect 100
        min_score = min(profile.values()) if profile else 100
        
        # Absolute Score Definitions
        ABS_LOW_THRESHOLD = 60
        CRITICAL_LOW = 40
        VERY_HIGH_THRESHOLD = 85

        for trait, score in profile.items():
            if trait not in self.MODULE_MAPPING:
                continue

            mapping = self.MODULE_MAPPING[trait]
            trait_name = mapping.get("name", trait.replace("_", " ").title())
            
            target_modules = []
            priority = "medium"
            reason_suffix = ""

            # --- LOGIC SELECTION ---
            if score > VERY_HIGH_THRESHOLD and "high_modules" in mapping:
                # 1. Very High - Priority Medium (Balance Needed)
                target_modules = mapping.get("high_modules", [])
                priority = "medium"
                reason_suffix = f"This is recommended to balance your very high {trait_name} score."

            elif score < ABS_LOW_THRESHOLD:
                # 2. Absolute Low - Priority High/Medium (Remedial)
                target_modules = mapping.get("low_modules", [])
                priority = "high" if score < CRITICAL_LOW else "medium"
                reason_suffix = f"This is Identified as a primary development area for {trait_name}."
            
            elif score == min_score and score < 100:
                # 3. Comparative Low - Priority Medium (Relative Weakness)
                # Only trigger if not already handled as High or Very High
                target_modules = mapping.get("low_modules", [])
                priority = "medium"
                reason_suffix = f"This trait is comparatively lower than your other strengths in {trait_name}."

            # --- POPULATE MODULES ---
            for mod_info in target_modules:
                recommendations.append(
                    ModuleRecommendation(
                        module=mod_info["name"],
                        reason=f"{mod_info['reason']} {reason_suffix}",
                        priority=priority,
                    )
                )

        # Sort: priority high first, then alphabetical for consistent delivery
        return sorted(recommendations, key=lambda x: (x.priority == "high"), reverse=True)

    def _get_trait_level(self, score: float) -> str:
        """Categorizes a score into high, moderate, or low based on specified thresholds."""
        if score >= 80:
            return "high"
        elif score >= 60:
            return "moderate"
        else:
            return "low"

    def _identify_strengths_and_areas(self, profile: dict[str, float], weak_traits: list[str]) -> tuple[list[str], list[str]]:
        """Identifies strengths (>=80) and development areas (weak_traits or <60)."""
        strengths = []
        development_areas = []
        
        for trait_key, score in profile.items():
            display_name = trait_key.replace("_", " ").title()
            if score >= 80:
                strengths.append(display_name)
            elif score < 60 or display_name in weak_traits:
                development_areas.append(display_name)
                
        # Remove duplicates while preserving order
        return list(dict.fromkeys(strengths)), list(dict.fromkeys(development_areas))

    def _calculate_overall_score(self, profile_scores: dict[str, float]) -> float:
        # Simple average of the 6 HEXACO traits (since each trait is 0-100)
        traits = ["honesty_humility", "emotionality", "extraversion", "agreeableness", "conscientiousness", "openness"]
        scores = [profile_scores.get(t, 0.0) for t in traits]
        return sum(scores) / len(traits) if traits else 0.0

    async def update_learning_path(self, user_id: UUID, recommendations: List[ModuleRecommendation]):
        # Call Learning Path Service (Vaaheesan)
        # Note: Vaaheesan should plug in learning_path_client here.
        payload = [{
            'name': r.module,
            'source': 'behavioral_assessment',
            'priority': r.priority,
            'reason': r.reason
        } for r in recommendations]
        
        # await learning_path_client.add_modules(user_id=user_id, modules=payload)
        pass

    async def report_completion(self, user_id: UUID, profile_scores: dict[str, float]):
        # Call Progress Tracking (Krishanth)
        # Note: Krishanth should plug in progress_tracking_client here.
        overall_score = self._calculate_overall_score(profile_scores)
        
        metadata = {'hexaco_profile': profile_scores}
        
        # await progress_tracking_client.record(
        #     user_id=user_id,
        #     module='behavioral',
        #     topic='hexaco_assessment',
        #     score=overall_score,
        #     metadata=metadata
        # )
        pass

    async def process_assessment_completion(
        self, db: AsyncSession, user_id: UUID, session_id: UUID
    ) -> BehavioralCompleteResponse:
        
        # 1. Fetch scores from session
        scores_result = await self.get_session_scores(db, session_id)

        # 2. Calculate HEXACO profile
        hexaco_profile = self.calculate_hexaco_profile(scores_result)

        # 3. Personality Report
        # Reusing the AI analysis already generated during the 'calculate_result' step.
        # This avoid making a second expensive LLM call for the same data.
        ai_report = scores_result.get("ai_analysis", {})

        # 4. Map to recommended modules
        recommendations = self.generate_recommendations(hexaco_profile)

        # 5. Update learning path
        await self.update_learning_path(user_id, recommendations)

        # 6. Report to progress tracking
        await self.report_completion(user_id, hexaco_profile)

        # --- Persist the Behavioral Profile ---
        profile_stmt = select(BehavProfile).where(BehavProfile.user_id == user_id)
        profile_result = await db.execute(profile_stmt)
        profile = profile_result.scalar_one_or_none()

        # Identify strengths and development areas using the new strategy
        weak_traits_display = scores_result.get("weak_traits", [])
        strengths, development_areas = self._identify_strengths_and_areas(hexaco_profile, weak_traits_display)
        
        ai_summary = ai_report.get("summary", "") if isinstance(ai_report, dict) else str(ai_report)

        if not profile:
            profile = BehavProfile(
                user_id=user_id,
                session_id=session_id,
                hexaco_scores=hexaco_profile,
                ai_report=ai_summary,
                recommended_modules=[r.model_dump() for r in recommendations],
                strengths=strengths,
                development_areas=development_areas,
                completed_at=datetime.utcnow(),
            )
            db.add(profile)
        else:
            profile.session_id = session_id
            profile.hexaco_scores = hexaco_profile
            profile.ai_report = ai_summary
            profile.recommended_modules = [r.model_dump() for r in recommendations]
            profile.strengths = strengths
            profile.development_areas = development_areas
            profile.completed_at = datetime.utcnow()

        await db.commit()

        return BehavioralCompleteResponse(
            user_id=user_id,
            hexaco_profile=hexaco_profile,
            personality_summary=ai_summary,
            recommended_modules=recommendations,
            learning_path_updated=True,
        )

    async def get_user_profile(self, db: AsyncSession, user_id: UUID) -> BehavioralProfileResponse:
        stmt = select(BehavProfile).where(BehavProfile.user_id == user_id)
        result = await db.execute(stmt)
        profile = result.scalar_one_or_none()

        if not profile:
            raise ValueError("Behavioral profile not found for user")

        formatted_scores = {}
        for trait, score in profile.hexaco_scores.items():
            level = self._get_trait_level(score)
            formatted_scores[trait] = TraitScore(score=score, level=level)

        return BehavioralProfileResponse(
            user_id=profile.user_id,
            completed_at=profile.completed_at,
            hexaco_scores=formatted_scores,
            strengths=profile.strengths or [],
            development_areas=profile.development_areas or [],
            ai_personality_report=profile.ai_report or "",
            needs_adaptive_test=len(profile.development_areas or []) > 0,
        )

    async def get_recommendations(self, db: AsyncSession, user_id: UUID) -> List[ModuleRecommendation]:
        stmt = select(BehavProfile).where(BehavProfile.user_id == user_id)
        result = await db.execute(stmt)
        profile = result.scalar_one_or_none()

        if not profile or not profile.recommended_modules:
            return []

        return [ModuleRecommendation(**r) for r in profile.recommended_modules]


behav_learning_service = BehavioralLearningService()

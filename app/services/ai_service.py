"""
AI Service for generating narrative feedback and analysis.
Handles GPT-based text generation for interview reports.
"""
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.config.settings import get_settings


def get_llm():
    """Initialize the LLM (GPT-4o-mini or fallback)."""
    settings = get_settings()
    return ChatOpenAI(
        model="gpt-4o-mini",
        api_key=settings.openai_api_key,
        temperature=0.7,
    )


async def generate_narrative_ai(
    interview_type: str,
    overall_score: float,
    strengths: list[dict],
    improvements: list[dict],
    question_count: int,
) -> str:
    """
    Generate a natural language narrative summary of interview performance.
    
    Args:
        interview_type: Type of interview (e.g., "Technical", "Behavioral", "General")
        overall_score: Overall performance score (0-100)
        strengths: List of identified strengths dictionaries [{"area": "...", "description": "...", "evidence": "..."}]
        improvements: List of improvement areas with structure {"area": "...", "description": "...", "recommendation": "...", "priority": "..."}
        question_count: Number of questions answered
    
    Returns:
        A narrative string summarizing the interview performance.
    """
    try:
        llm = get_llm()

        # Format improvement areas
        improvement_text = "\n".join(
            [f"- {imp.get('area', 'Unknown')}: {imp.get('description', '')}" for imp in improvements[:3]]
        )

        # Create a prompt for the narrative
        prompt_template = ChatPromptTemplate.from_template(
            """Generate a brief, professional narrative summary (2-3 sentences) of an interview performance based on:

Interview Type: {interview_type}
Overall Score: {overall_score}/100
Questions Answered: {question_count}
Performance Level: {performance_level}

Identified Strengths:
{strengths}

Areas for Improvement:
{improvement_text}

Provide an encouraging yet honest assessment that highlights key performance indicators and actionable next steps."""
        )

        # Determine performance level
        if overall_score >= 80:
            performance_level = "Excellent"
        elif overall_score >= 70:
            performance_level = "Good"
        elif overall_score >= 60:
            performance_level = "Satisfactory"
        else:
            performance_level = "Needs Improvement"

        # Format strengths
        strengths_text = "\n".join([f"- {s.get('area', 'General')}: {s.get('description', '')}" for s in strengths[:3]]) if strengths else "- Communication clarity"

        # Create the prompt chain
        chain = prompt_template | llm

        # Generate the narrative
        result = await chain.ainvoke({
            "interview_type": interview_type,
            "overall_score": overall_score,
            "performance_level": performance_level,
            "question_count": question_count,
            "strengths": strengths_text,
            "improvement_text": improvement_text or "- Continue practicing interview techniques"
        })

        return str(result.content).strip()

    except Exception:
        # Fallback if AI call fails
        return f"Interview completed with a score of {overall_score}/100. Continue practicing to improve performance."

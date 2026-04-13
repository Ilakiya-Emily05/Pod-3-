import logging
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.pronunciation import PhonemePerformance, UserPronunciationProfile
from app.services.leveling import LEVEL_REQUIREMENTS

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/pronunciation", tags=["Pronunciation"])

# ── Practice sentence bank ────────────────────────────────────────────────────
SENTENCE_BANK: dict[str, list[dict]] = {
    "θ": [
        {"sentence": "Think about the thing.", "difficulty": "basic"},
        {"sentence": "Three thousand thoughts.", "difficulty": "intermediate"},
        {
            "sentence": "The thermometer showed the temperature throughout the month.",
            "difficulty": "advanced",
        },
    ],
    "ð": [
        {"sentence": "This is the day that they arrived.", "difficulty": "basic"},
        {"sentence": "Those weathered clothes are theirs.", "difficulty": "intermediate"},
        {
            "sentence": "Although the weather was smooth, they gathered together.",
            "difficulty": "advanced",
        },
    ],
    "ə": [
        {"sentence": "The problem was about a banana.", "difficulty": "basic"},
        {"sentence": "A collection of unusual animals.", "difficulty": "intermediate"},
        {
            "sentence": "The opposition presented an elaborate and reasonable proposal.",
            "difficulty": "advanced",
        },
    ],
    "f": [
        {"sentence": "Five frogs fled from the fog.", "difficulty": "basic"},
        {
            "sentence": "The effort to perfect the draft was effective.",
            "difficulty": "intermediate",
        },
        {
            "sentence": "The professor offered a profound and influential lecture.",
            "difficulty": "advanced",
        },
    ],
    "m": [
        {"sentence": "Make my mother some lemon jam.", "difficulty": "basic"},
        {"sentence": "The minimum amount was met immediately.", "difficulty": "intermediate"},
        {
            "sentence": "The momentum of the movement impressed many members.",
            "difficulty": "advanced",
        },
    ],
    "l": [
        {"sentence": "Lucy likes light blue balloons.", "difficulty": "basic"},
        {"sentence": "The tall fellow left the village slowly.", "difficulty": "intermediate"},
    ],
    "i": [
        {"sentence": "She sees three green trees.", "difficulty": "basic"},
        {"sentence": "He believes the team will achieve the lead.", "difficulty": "intermediate"},
        {
            "sentence": "The elite athlete competed fiercely to seize the lead.",
            "difficulty": "advanced",
        },
    ],
    "oʊ": [
        {"sentence": "Go home and open the old stove.", "difficulty": "basic"},
        {"sentence": "The cold stone road goes below the slope.", "difficulty": "intermediate"},
        {"sentence": "The devoted poet composed an ode about the ocean.", "difficulty": "advanced"},
    ],
    "d": [
        {"sentence": "Dad did a good deed today.", "difficulty": "basic"},
        {
            "sentence": "David decided to add the details to the document.",
            "difficulty": "intermediate",
        },
        {
            "sentence": "The dedicated doctor devoted decades to medical advancement.",
            "difficulty": "advanced",
        },
    ],
    "z": [
        {"sentence": "Zoe sees zebras at the zoo.", "difficulty": "basic"},
        {"sentence": "The buzzing noise caused a dozen problems.", "difficulty": "intermediate"},
        {
            "sentence": "The organization realized its goals through amazing teamwork.",
            "difficulty": "advanced",
        },
    ],
    "w": [
        {"sentence": "We will walk with the wind.", "difficulty": "basic"},
        {"sentence": "Would you wait while I wash the window?", "difficulty": "intermediate"},
        {
            "sentence": "The witnesserwhelmed the crowd with powerful and wise words.",
            "difficulty": "advanced",
        },
    ],
    "r": [
        {"sentence": "Run around the red river.", "difficulty": "basic"},
        {
            "sentence": "The rural road required repairs after the rain.",
            "difficulty": "intermediate",
        },
        {
            "sentence": "The researcher retrieved remarkable results from the rare records.",
            "difficulty": "advanced",
        },
    ],
    "n": [
        {"sentence": "Nine new notebooks near the window.", "difficulty": "basic"},
        {"sentence": "Neither of the knives needs cleaning now.", "difficulty": "intermediate"},
        {
            "sentence": "The renowned engineer announced an innovative new invention.",
            "difficulty": "advanced",
        },
    ],
    "dʒ": [
        {"sentence": "Just enjoy the job.", "difficulty": "basic"},
        {"sentence": "The judge rejected the major changes.", "difficulty": "intermediate"},
        {
            "sentence": "The journalist managed to engage the younger generation.",
            "difficulty": "advanced",
        },
    ],
    "ɔɪ": [
        {"sentence": "The boy enjoyed the toy.", "difficulty": "basic"},
        {"sentence": "Roy avoided the noisy oil joint.", "difficulty": "intermediate"},
        {
            "sentence": "The loyal employee voiced his choice to the employer.",
            "difficulty": "advanced",
        },
    ],
    "ɪ": [
        {"sentence": "It is a big fish dish.", "difficulty": "basic"},
        {"sentence": "The village is built on a hilly ridge.", "difficulty": "intermediate"},
        {
            "sentence": "The physicist insisted on a significant and rigid distinction.",
            "difficulty": "advanced",
        },
    ],
    "ŋ": [
        {"sentence": "Sing a long song this evening.", "difficulty": "basic"},
        {
            "sentence": "The ringing and clanging was getting stronger.",
            "difficulty": "intermediate",
        },
        {
            "sentence": "The challenging undertaking was both demanding and rewarding.",
            "difficulty": "advanced",
        },
    ],
    "s": [
        {"sentence": "Sam sells sea shells by the sea shore.", "difficulty": "basic"},
        {
            "sentence": "The scientist stressed the success of the system.",
            "difficulty": "intermediate",
        },
        {
            "sentence": "The assistant assessed the serious circumstances with precision.",
            "difficulty": "advanced",
        },
    ],
    "æ": [
        {"sentence": "The cat sat on the black mat.", "difficulty": "basic"},
        {
            "sentence": "Ann has a bad habit of clapping hands rapidly.",
            "difficulty": "intermediate",
        },
        {
            "sentence": "The athlete cracked a practical and abstract plan of action.",
            "difficulty": "advanced",
        },
    ],
    "p": [
        {"sentence": "Peter picked a pack of peppers.", "difficulty": "basic"},
        {
            "sentence": "The puppet performance appeared pretty impressive.",
            "difficulty": "intermediate",
        },
        {
            "sentence": "The expert proposed a practical approach to improve productivity.",
            "difficulty": "advanced",
        },
    ],
    "b": [
        {"sentence": "Bob bought a big blue bag.", "difficulty": "basic"},
        {
            "sentence": "The baby grabbed the rubber ball beside the bed.",
            "difficulty": "intermediate",
        },
        {
            "sentence": "The ambitious builder observed the problem and rebuilt the structure.",
            "difficulty": "advanced",
        },
    ],
    "t": [
        {"sentence": "Take the train to town today.", "difficulty": "basic"},
        {"sentence": "The tourist took a taste of the tasty tart.", "difficulty": "intermediate"},
        {
            "sentence": "The architect attempted to estimate the total cost of the project.",
            "difficulty": "advanced",
        },
    ],
    "k": [
        {"sentence": "Keep the cat in the kitchen.", "difficulty": "basic"},
        {
            "sentence": "The colorful kite caught the cool breeze quickly.",
            "difficulty": "intermediate",
        },
        {
            "sentence": "The technical committee acknowledged the complex and critical conflict.",
            "difficulty": "advanced",
        },
    ],
    "g": [
        {"sentence": "Get the big green bag.", "difficulty": "basic"},
        {
            "sentence": "The goat grabbed the green grass near the garden gate.",
            "difficulty": "intermediate",
        },
        {
            "sentence": "The geologist suggested the biggest geological discovery of the decade.",
            "difficulty": "advanced",
        },
    ],
    "v": [
        {"sentence": "Vivian loves to visit every valley.", "difficulty": "basic"},
        {
            "sentence": "The driver moved the vehicle over the curved road.",
            "difficulty": "intermediate",
        },
        {
            "sentence": "The investigator revealed the involvement of several individuals.",
            "difficulty": "advanced",
        },
    ],
    "h": [
        {"sentence": "He held his hat in his hand.", "difficulty": "basic"},
        {
            "sentence": "The happy hiker headed home through the hills.",
            "difficulty": "intermediate",
        },
        {
            "sentence": "The historian highlighted the heroic achievements of the inhabitants.",
            "difficulty": "advanced",
        },
    ],
    "j": [
        {"sentence": "Yes you can use your yellow yacht.", "difficulty": "basic"},
        {"sentence": "The young student yearned for years to play.", "difficulty": "intermediate"},
        {
            "sentence": "The youthful musician yearned to yield beautiful and unique melodies.",
            "difficulty": "advanced",
        },
    ],
    "ʃ": [
        {"sentence": "She sells shells at the shore.", "difficulty": "basic"},
        {
            "sentence": "The sharp shadow showed the shape of the shed.",
            "difficulty": "intermediate",
        },
        {
            "sentence": "The official established a special commission to finish the research.",
            "difficulty": "advanced",
        },
    ],
    "tʃ": [
        {"sentence": "Charles chose to eat peach and cheese.", "difficulty": "basic"},
        {
            "sentence": "The teacher challenged each child to reach their potential.",
            "difficulty": "intermediate",
        },
        {
            "sentence": "The architect sketched each arch and notched each structural breach.",
            "difficulty": "advanced",
        },
    ],
    "ʒ": [
        {"sentence": "It was a usual pleasure.", "difficulty": "basic"},
        {
            "sentence": "The beige garage had a casual and leisurely atmosphere.",
            "difficulty": "intermediate",
        },
        {
            "sentence": "The prestigious vision brought a measure of exposure to the regime.",
            "difficulty": "advanced",
        },
    ],
    "aɪ": [
        {"sentence": "I like to fly kites at night.", "difficulty": "basic"},
        {
            "sentence": "The bright light guided my eyes through the wide sky.",
            "difficulty": "intermediate",
        },
        {
            "sentence": "The scientist tried to identify the precise climate inside the island.",
            "difficulty": "advanced",
        },
    ],
    "aʊ": [
        {"sentence": "How now brown cow.", "difficulty": "basic"},
        {
            "sentence": "The loud crowd gathered around the south mountain town.",
            "difficulty": "intermediate",
        },
        {
            "sentence": "The renowned accountant announced the astounding amount aloud.",
            "difficulty": "advanced",
        },
    ],
    "ʌ": [
        {"sentence": "The sun comes up above the mud.", "difficulty": "basic"},
        {
            "sentence": "The young monk studied until the summer was done.",
            "difficulty": "intermediate",
        },
        {
            "sentence": "The sudden thunder disrupted the wonderful discussion among us.",
            "difficulty": "advanced",
        },
    ],
    "ʊ": [
        {"sentence": "Look at the good book.", "difficulty": "basic"},
        {
            "sentence": "The woman stood by the wooden foot of the brook.",
            "difficulty": "intermediate",
        },
        {
            "sentence": "The cook mistook the sugar for flour and could not undo it.",
            "difficulty": "advanced",
        },
    ],
    "u": [
        {"sentence": "Move the blue shoe to the room.", "difficulty": "basic"},
        {
            "sentence": "The smooth music from the flute flew through the school.",
            "difficulty": "intermediate",
        },
        {
            "sentence": "The nutritious fruit improved the mood of the youth group.",
            "difficulty": "advanced",
        },
    ],
    "ɛ": [
        {"sentence": "Get the red pen off the desk.", "difficulty": "basic"},
        {
            "sentence": "The healthy men meant to measure the length carefully.",
            "difficulty": "intermediate",
        },
        {
            "sentence": "The expert expressed concern about the extent of the debt.",
            "difficulty": "advanced",
        },
    ],
    "ɑ": [
        {"sentence": "The father watched the calm dark water.", "difficulty": "basic"},
        {
            "sentence": "The honest artist carved a large marble heart.",
            "difficulty": "intermediate",
        },
        {
            "sentence": "The calm architect designed a large landmark for the harbour.",
            "difficulty": "advanced",
        },
    ],
    "ɔ": [
        {"sentence": "The dog walked along the long hall.", "difficulty": "basic"},
        {
            "sentence": "The author often talked about the awesome autumn fog.",
            "difficulty": "intermediate",
        },
        {
            "sentence": "The lawyer thought the law brought more order to the audience.",
            "difficulty": "advanced",
        },
    ],
    # ── Added missing phonemes ─────────────────────────────────────────────
    "e": [
        {"sentence": "They say it is a great day.", "difficulty": "basic"},
        {"sentence": "The weight of eight crates made them late.", "difficulty": "intermediate"},
        {
            "sentence": "The candidate demonstrated great patience and amazing debate skills.",
            "difficulty": "advanced",
        },
    ],
    "ɾ": [
        {"sentence": "The butter was better this time.", "difficulty": "basic"},
        {
            "sentence": "The writer had a better attitude toward the matter.",
            "difficulty": "intermediate",
        },
        {
            "sentence": "The bitter winter weather battered the outer shelter repeatedly.",
            "difficulty": "advanced",
        },
    ],
}


def _compute_next_milestone(profile: UserPronunciationProfile) -> str:
    lp = profile.level_progress or {}
    exercises_at_level = int(lp.get("exercises_at_level", 0))
    required = int(
        lp.get("required_for_next", LEVEL_REQUIREMENTS.get(profile.current_level or "basic", 20))
    )
    remaining = max(0, required - exercises_at_level)

    if remaining == 0:
        return "You are eligible to level up! Keep your average score above 70%."
    return f"Complete {remaining} more exercise(s) at this level to progress."


@router.get(
    "/recommendations/{user_id}",
    summary="Get personalised pronunciation recommendations",
)
def get_pronunciation_recommendations(user_id: uuid.UUID, db: Session = Depends(get_db)):
    profile = (
        db.query(UserPronunciationProfile)
        .filter(UserPronunciationProfile.user_id == user_id)
        .first()
    )

    if not profile:
        return {
            "focus_areas": [],
            "suggested_practice_time_mins": 10,
            "next_milestone": "No data yet. Complete your first exercise to get recommendations.",
        }

    # Current level for difficulty filtering
    level = profile.current_level or "basic"

    # Fetch weak phonemes from live performance data
    weak_rows = (
        db.query(PhonemePerformance)
        .filter(
            PhonemePerformance.user_id == user_id,
            PhonemePerformance.accuracy_pct < 50,
        )
        .order_by(PhonemePerformance.accuracy_pct.asc())  # worst first
        .all()
    )

    focus_areas = []
    for row in weak_rows:
        exercises = SENTENCE_BANK.get(row.phoneme, [])
        if not exercises:
            continue

        # Filter to user's current level
        filtered = [e for e in exercises if e["difficulty"] == level]
        if not filtered:
            filtered = exercises  # fallback to all if none match level

        focus_areas.append(
            {
                "phoneme": row.phoneme,
                "accuracy_pct": float(row.accuracy_pct or 0),
                "exercises": filtered,
            }
        )

    # Suggested practice time: 5 min base + 3 min per weak phoneme (max 30)
    suggested_mins = min(30, 5 + len(focus_areas) * 3)

    return {
        "user_level": level,
        "focus_areas": focus_areas,
        "suggested_practice_time_mins": suggested_mins,
        "next_milestone": _compute_next_milestone(profile),
    }

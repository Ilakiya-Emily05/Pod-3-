from enum import StrEnum


class AttemptStatus(StrEnum):
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    EVALUATED = "evaluated"


class CEFRLevel(StrEnum):
    A1 = "A1"
    A2 = "A2"
    B1 = "B1"
    B2 = "B2"
    C1 = "C1"
    C2 = "C2"


def is_valid_cefr_result_level(value: str) -> bool:
    """Return whether a CEFR result value is valid.

    Allows base CEFR levels (A1-C2) and promoted levels (for example, B1+).
    """
    base_values = {level.value for level in CEFRLevel}
    if value in base_values:
        return True
    if len(value) != 3:
        return False
    if not value.endswith("+"):
        return False
    return value[:2] in base_values

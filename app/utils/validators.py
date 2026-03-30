"""Reusable validators for Pydantic schemas."""

from app.models.assessment_status import is_valid_cefr_result_level


def validate_cefr_result_level(value: str | None) -> str | None:
    """Validate CEFR result level field.

    Allows base CEFR levels (A1-C2) and promoted levels (for example, B1+).

    Args:
        value: The CEFR result level to validate.

    Returns:
        The validated value, or None if input is None.

    Raises:
        ValueError: If the value is not a valid CEFR result level.
    """
    if value is None:
        return None
    if not is_valid_cefr_result_level(value):
        msg = f"Invalid CEFR result level: {value}"
        raise ValueError(msg)
    return value

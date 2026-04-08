_models_registered = False


def register_models() -> None:
    """Register all models with SQLAlchemy's MetaData. Safe to call multiple times."""
    global _models_registered

    if _models_registered:
        return

    # ── New analytics models (Sprint 2 Task 1) ────────────────────

    _models_registered = True

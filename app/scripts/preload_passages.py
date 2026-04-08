from app.config.database import get_db
from app.services.passage_service import PassageService

TARGET_POOL = 50


def main() -> None:
    db_gen = get_db()
    db = next(db_gen)

    try:
        service = PassageService(db)
        before = service.repo.count_passages()
        service.preload_passages(TARGET_POOL)
        after = service.repo.count_passages()
        print(f"Passage preload complete. Before={before}, After={after}, Added={after - before}")
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass


if __name__ == "__main__":
    main()

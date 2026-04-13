from app.services.vocabulary_service import calculate_sm2


def test_sm2_failure_quality_low_changes_easiness():
    new_e, _new_r, new_i = calculate_sm2(quality=2, easiness=2.5, repetitions=2, interval=1)
    assert new_i == 1
    assert new_e <= 2.5
    assert new_e >= 1.3


def test_sm2_first_repetitions_intervals_and_easiness_increase():
    new_e1, _new_r1, new_i1 = calculate_sm2(quality=5, easiness=2.5, repetitions=0, interval=1)
    assert new_i1 == 1
    assert new_e1 > 2.5

    new_e2, _new_r2, new_i2 = calculate_sm2(
        quality=5, easiness=new_e1, repetitions=1, interval=new_i1
    )
    assert new_i2 == 8  # 6 * 1.3 (easy boost)
    assert new_e2 > new_e1


def test_sm2_later_repetition_interval_growth():
    new_e, _new_r, new_i = calculate_sm2(quality=4, easiness=2.7, repetitions=3, interval=10)
    assert new_i >= 1
    assert new_e >= 1.3

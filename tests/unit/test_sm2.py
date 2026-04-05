import pytest

from app.services.vocabulary_service import _sm2_next_interval


def test_sm2_failure_quality_low_changes_easiness():
    interval, new_e = _sm2_next_interval(rep=2, quality=2, easiness=2.5)
    assert interval == 0
    assert new_e <= 2.5
    assert new_e >= 1.3


def test_sm2_first_repetitions_intervals_and_easiness_increase():
    interval1, e1 = _sm2_next_interval(rep=0, quality=5, easiness=2.5)
    assert interval1 == 1
    assert e1 > 2.5

    interval2, e2 = _sm2_next_interval(rep=1, quality=5, easiness=e1)
    assert interval2 == 6
    assert e2 > e1


def test_sm2_later_repetition_interval_growth():
    interval, new_e = _sm2_next_interval(rep=3, quality=4, easiness=2.7)
    assert interval >= 1
    assert new_e >= 1.3

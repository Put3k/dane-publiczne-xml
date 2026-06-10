from datetime import date

from _fill_the_gap import find_gaps


def d(day):
    return date(2026, 6, day)


def test_interior_gap_fills_from_day_after():
    existing = {d(1), d(2), d(4)}
    assert find_gaps(existing, d(1), d(4)) == [(d(3), d(4))]


def test_consecutive_gaps_share_nearest_successor():
    existing = {d(1), d(4)}
    assert find_gaps(existing, d(1), d(4)) == [(d(2), d(4)), (d(3), d(4))]


def test_gap_at_date_to_is_unfillable():
    # 06-03 has no later day within the window -> omitted
    existing = {d(1), d(2)}
    assert find_gaps(existing, d(1), d(3)) == []


def test_no_gaps():
    existing = {d(1), d(2), d(3)}
    assert find_gaps(existing, d(1), d(3)) == []


def test_successor_must_be_within_date_to():
    # a real day exists at 06-05 but it is past date_to, so nothing is fillable
    existing = {d(1), d(5)}
    assert find_gaps(existing, d(1), d(3)) == []

from __future__ import annotations

from datetime import date, timedelta

from models import Review
from services.quiz import next_review


def test_first_success_is_scheduled_tomorrow():
    review = next_review(None, 5)
    assert review.interval_days == 1
    assert review.reps == 1
    assert review.lapses == 0
    assert review.due_at == (date.today() + timedelta(days=1)).isoformat()
    assert review.ease == 2.6


def test_second_success_moves_to_three_days():
    first = Review(question_id="q", due_at=date.today().isoformat(), interval_days=1, ease=2.6, reps=1)
    second = next_review(first, 5)
    assert second.interval_days == 3
    assert second.reps == 2


def test_later_success_multiplies_by_ease():
    review = Review(question_id="q", due_at=date.today().isoformat(), interval_days=3, ease=2.7, reps=2)
    result = next_review(review, 4)
    assert result.interval_days == round(3 * 2.7)
    assert result.reps == 3


def test_failure_resets_and_counts_lapse():
    review = Review(question_id="q", due_at=date.today().isoformat(), interval_days=9, ease=2.4, reps=4)
    result = next_review(review, 2)
    assert result.interval_days == 1
    assert result.reps == 0
    assert result.lapses == 1
    assert result.ease < 2.4
    assert result.ease >= 1.3


def test_ease_is_clamped():
    review = Review(question_id="q", due_at=date.today().isoformat(), interval_days=1, ease=1.3, reps=0)
    result = next_review(review, 0)
    assert result.ease == 1.3
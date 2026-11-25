from __future__ import annotations

from models import STATUS_LEARNING, STATUS_MASTERED, STATUS_TODO
from services.learning import compute_mastery


def test_mastery_requires_lesson_and_score():
    mastery, status = compute_mastery(True, [100])
    assert mastery == 100
    assert status == STATUS_MASTERED


def test_high_score_without_lesson_is_not_mastered():
    mastery, status = compute_mastery(False, [100])
    assert mastery == 80
    assert status == STATUS_LEARNING


def test_mastery_uses_best_and_recent_three():
    mastery, _ = compute_mastery(True, [40, 80, 90, 100, 70])
    assert mastery == round(20 + 100 * 0.5 + (90 + 100 + 70) / 3 * 0.3)


def test_no_activity_is_todo():
    mastery, status = compute_mastery(False, [])
    assert mastery == 0
    assert status == STATUS_TODO


def test_scores_are_clamped():
    mastery, status = compute_mastery(True, [150, -20])
    assert 0 <= mastery <= 100
    assert status in {STATUS_LEARNING, STATUS_MASTERED}
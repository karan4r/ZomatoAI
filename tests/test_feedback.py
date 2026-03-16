"""Tests for Phase 6 feedback collection."""

import pytest
from zomato_ai.feedback import (
    clear_feedback,
    get_feedback_events,
    record_feedback,
)


def test_record_and_get_feedback():
    clear_feedback()
    record_feedback(restaurant_id=101, action="clicked", user_id="u1")
    record_feedback(restaurant_id=102, action="liked", user_id="u1")
    events = get_feedback_events(limit=10)
    assert len(events) == 2
    assert events[0].restaurant_id == 101 and events[0].action == "clicked"
    assert events[1].restaurant_id == 102 and events[1].action == "liked"


def test_clear_feedback():
    record_feedback(restaurant_id=1, action="dismissed")
    clear_feedback()
    assert len(get_feedback_events()) == 0

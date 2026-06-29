import pytest

from src.services import handoff_service
from src.services.handoff_service import (
    HANDOFF_STATUS_ACCEPTED,
    HANDOFF_STATUS_COMPLETED,
    HANDOFF_STATUS_FAILED,
    HANDOFF_STATUS_GENERATING,
    HANDOFF_STATUS_READY,
    HANDOFF_STATUS_REQUESTED,
    is_active_handoff,
    validate_transition,
)


class TestStatusMachine:
    def test_active_handoff_includes_pre_completion(self):
        assert is_active_handoff(HANDOFF_STATUS_REQUESTED) is True
        assert is_active_handoff(HANDOFF_STATUS_GENERATING) is True
        assert is_active_handoff(HANDOFF_STATUS_READY) is True
        assert is_active_handoff(HANDOFF_STATUS_ACCEPTED) is True
        assert is_active_handoff(HANDOFF_STATUS_COMPLETED) is False
        assert is_active_handoff(HANDOFF_STATUS_FAILED) is False

    def test_valid_transitions(self):
        validate_transition(HANDOFF_STATUS_REQUESTED, HANDOFF_STATUS_GENERATING)
        validate_transition(HANDOFF_STATUS_GENERATING, HANDOFF_STATUS_READY)
        validate_transition(HANDOFF_STATUS_READY, HANDOFF_STATUS_ACCEPTED)
        validate_transition(HANDOFF_STATUS_ACCEPTED, HANDOFF_STATUS_COMPLETED)
        validate_transition(HANDOFF_STATUS_REQUESTED, HANDOFF_STATUS_FAILED)
        validate_transition(HANDOFF_STATUS_READY, HANDOFF_STATUS_FAILED)

    def test_invalid_transition_raises(self):
        with pytest.raises(handoff_service.HandoffValidationError):
            validate_transition(HANDOFF_STATUS_REQUESTED, HANDOFF_STATUS_READY)
        with pytest.raises(handoff_service.HandoffValidationError):
            validate_transition(HANDOFF_STATUS_READY, HANDOFF_STATUS_COMPLETED)
        with pytest.raises(handoff_service.HandoffValidationError):
            validate_transition(HANDOFF_STATUS_COMPLETED, HANDOFF_STATUS_REQUESTED)

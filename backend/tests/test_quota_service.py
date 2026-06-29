import pytest
from src.services import quota_service
from src.models.quota import QuotaRecord


def _make_record(**kwargs) -> QuotaRecord:
    defaults = {
        "provider": "openai",
        "model_id": "gpt-4o",
        "model_name": "GPT-4o",
        "request_count": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
        "limit_error_count": 0,
        "handoff_triggered_count": 0,
        "quota_mode": "unknown",
        "quota_status": "unknown",
    }
    defaults.update(kwargs)
    return QuotaRecord(**defaults)


class TestCalculateUsagePercent:
    def test_known_mode_with_limit(self):
        record = _make_record(
            quota_mode="known", token_limit=10000, total_tokens=5000,
        )
        assert quota_service._calculate_usage_percent(record) == 0.5

    def test_known_mode_no_limit(self):
        record = _make_record(
            quota_mode="known", token_limit=None, total_tokens=5000,
        )
        assert quota_service._calculate_usage_percent(record) is None

    def test_unknown_mode(self):
        record = _make_record(
            quota_mode="unknown", total_tokens=5000,
        )
        assert quota_service._calculate_usage_percent(record) is None


class TestDetermineQuotaStatus:
    def test_normal(self):
        record = _make_record(
            quota_mode="known", token_limit=10000, total_tokens=3000,
        )
        assert quota_service._determine_quota_status(record) == "normal"

    def test_warning(self):
        record = _make_record(
            quota_mode="known", token_limit=10000, total_tokens=7500,
        )
        assert quota_service._determine_quota_status(record) == "warning"

    def test_near_limit(self):
        record = _make_record(
            quota_mode="known", token_limit=10000, total_tokens=9500,
        )
        assert quota_service._determine_quota_status(record) == "near_limit"

    def test_limited_by_usage(self):
        record = _make_record(
            quota_mode="known", token_limit=10000, total_tokens=12000,
        )
        assert quota_service._determine_quota_status(record) == "limited"

    def test_limited_by_error(self):
        record = _make_record(
            quota_mode="unknown", limit_error_count=1,
        )
        assert quota_service._determine_quota_status(record) == "limited"

    def test_cooldown(self):
        from datetime import datetime, timezone, timedelta
        record = _make_record(
            quota_mode="known", token_limit=10000, total_tokens=5000,
            cooldown_until=datetime.now(timezone.utc) + timedelta(minutes=5),
        )
        assert quota_service._determine_quota_status(record) == "cooldown"

    def test_unknown_no_requests(self):
        record = _make_record(
            quota_mode="unknown", request_count=0,
        )
        assert quota_service._determine_quota_status(record) == "unknown"

    def test_unknown_with_requests(self):
        record = _make_record(
            quota_mode="unknown", request_count=5,
        )
        assert quota_service._determine_quota_status(record) == "normal"


class TestBuildRiskFlags:
    def test_near_limit_flag(self):
        record = _make_record(quota_status="near_limit")
        assert "near_quota_limit" in quota_service._build_risk_flags(record)

    def test_limited_flag(self):
        record = _make_record(quota_status="limited")
        assert "quota_exhausted" in quota_service._build_risk_flags(record)

    def test_normal_no_flags(self):
        record = _make_record(quota_status="normal")
        assert quota_service._build_risk_flags(record) == []


class TestIsLimitError:
    def test_429_is_limit(self):
        assert quota_service._is_limit_error(429, None) is True

    def test_402_is_limit(self):
        assert quota_service._is_limit_error(402, None) is True

    def test_200_not_limit(self):
        assert quota_service._is_limit_error(200, None) is False

    def test_insufficient_quota_type(self):
        assert quota_service._is_limit_error(None, "insufficient_quota") is True

    def test_none_not_limit(self):
        assert quota_service._is_limit_error(None, None) is False


class TestRecordUsageService:
    def test_record_successful_usage(self, db_session):
        result = quota_service.record_usage(
            db=db_session,
            provider="openai",
            model_id="gpt-4o",
            model_name="GPT-4o",
            total_tokens=1000,
        )
        # With request_count > 0 and no limit, status becomes normal
        assert result["updated_status"] == "normal"

    def test_record_with_rate_limit(self, db_session):
        result = quota_service.record_usage(
            db=db_session,
            provider="openai",
            model_id="gpt-4o",
            error_code=429,
        )
        assert result["updated_status"] == "cooldown"
        assert "rate_limited" in result["risk_flags"]

    def test_accumulates_requests(self, db_session):
        quota_service.record_usage(db=db_session, provider="openai", model_id="gpt-4o", total_tokens=100)
        quota_service.record_usage(db=db_session, provider="openai", model_id="gpt-4o", total_tokens=200)
        record = db_session.query(QuotaRecord).filter(QuotaRecord.model_id == "gpt-4o").first()
        assert record.request_count == 2
        assert record.total_tokens == 300


class TestUpdateQuotaConfig:
    def test_update_sets_known_mode(self, db_session):
        record = _make_record(request_count=5, total_tokens=5000)
        db_session.add(record)
        db_session.commit()

        result = quota_service.update_quota_config(
            db=db_session, model_id="gpt-4o", token_limit=10000
        )
        assert result["quota_mode"] == "known"
        assert result["token_limit"] == 10000
        assert result["usage_percent"] == 0.5

    def test_update_invalid_limit(self, db_session):
        record = _make_record()
        db_session.add(record)
        db_session.commit()

        with pytest.raises(quota_service.InvalidQuotaConfigError):
            quota_service.update_quota_config(
                db=db_session, model_id="gpt-4o", token_limit=0
            )

    def test_update_not_found(self, db_session):
        with pytest.raises(quota_service.QuotaNotFoundError):
            quota_service.update_quota_config(
                db=db_session, model_id="nonexistent", token_limit=10000
            )


class TestCheckAndIntercept:
    def test_intercepts_limited(self, db_session):
        record = _make_record(quota_status="limited")
        db_session.add(record)
        db_session.commit()

        result = quota_service.check_and_intercept(db_session, "gpt-4o")
        assert result["intercepted"] is True

    def test_no_intercept_normal(self, db_session):
        record = _make_record(quota_status="normal")
        db_session.add(record)
        db_session.commit()

        result = quota_service.check_and_intercept(db_session, "gpt-4o")
        assert result["intercepted"] is False

    def test_no_record_returns_none(self, db_session):
        result = quota_service.check_and_intercept(db_session, "nonexistent")
        assert result is None

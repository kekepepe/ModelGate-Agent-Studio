"""V1.0-3: design-aligned Station fields (slug / is_builtin / handoff_policy).

Per 2026-09-06-platform-redesign.md §4.1:

  - Every user-created station gets a unique auto-derived `slug`.
  - Built-in seeded stations are flagged `is_builtin=True`.
  - Built-in stations are protected from accidental deletion.
  - `handoff_policy` is a structured JSON dict surfaced in the
    response payload.
"""

import json

import pytest


# ---------------------------------------------------------------------------
# Slug auto-derivation
# ---------------------------------------------------------------------------

class TestSlugGeneration:
    def test_user_station_gets_auto_slug_from_name(self, client):
        resp = client.post("/api/v1/agents", json={
            "name": "My Cool Agent",
            "role": "coder",
            "default_model_id": "model-1",
        })
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["slug"] == "my-cool-agent"
        assert data["is_builtin"] is False

    def test_duplicate_name_gets_unique_suffix(self, client):
        client.post("/api/v1/agents", json={
            "name": "My Cool Agent",
            "role": "coder",
            "default_model_id": "model-1",
        })
        resp = client.post("/api/v1/agents", json={
            "name": "My Cool Agent",
            "role": "coder",
            "default_model_id": "model-1",
        })
        assert resp.status_code == 201
        assert resp.json()["data"]["slug"] == "my-cool-agent-2"

    def test_special_characters_normalised(self, client):
        resp = client.post("/api/v1/agents", json={
            "name": "  中文 @#$ Agent!! ",
            "role": "coder",
            "default_model_id": "model-1",
        })
        assert resp.status_code == 201
        # Non-ASCII characters and punctuation collapse into a single dash;
        # the final slug keeps only the ASCII alphanumeric runs ("agent").
        slug = resp.json()["data"]["slug"]
        assert slug == "agent"

    def test_empty_name_rejected(self, client):
        # Pydantic min_length=1 fires before service-level validation,
        # so the response is 422 (validation error), not 400.
        resp = client.post("/api/v1/agents", json={
            "name": "",
            "role": "coder",
            "default_model_id": "model-1",
        })
        assert resp.status_code in (400, 422)


# ---------------------------------------------------------------------------
# Built-in protection
# ---------------------------------------------------------------------------

class TestBuiltinProtection:
    def test_built_in_station_has_is_builtin_true(self, db_session, seed_builtin_station):
        station = seed_builtin_station(slug="planner")
        assert station.is_builtin is True
        assert station.slug == "planner"

    def test_user_station_has_is_builtin_false(self, client):
        resp = client.post("/api/v1/agents", json={
            "name": "User Agent",
            "role": "coder",
            "default_model_id": "model-1",
        })
        assert resp.json()["data"]["is_builtin"] is False

    def test_delete_builtin_station_is_rejected(self, client, db_session, seed_builtin_station):
        station = seed_builtin_station(slug="protected-planner")
        resp = client.delete(f"/api/v1/agents/{station.id}")
        assert resp.status_code == 400
        body = resp.json()
        assert body["detail"]["error"]["code"] == "BAD_REQUEST"
        assert "built-in" in body["detail"]["error"]["message"].lower()

    def test_delete_user_station_succeeds(self, client):
        create = client.post("/api/v1/agents", json={
            "name": "Disposable",
            "role": "coder",
            "default_model_id": "model-1",
        })
        agent_id = create.json()["data"]["id"]
        resp = client.delete(f"/api/v1/agents/{agent_id}")
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# handoff_policy structure
# ---------------------------------------------------------------------------

class TestHandoffPolicy:
    def test_user_station_default_handoff_policy(self, client):
        # The create response is intentionally minimal (id/slug/role/...),
        # so the test fetches the full record via GET to inspect the
        # handoff_policy.
        create = client.post("/api/v1/agents", json={
            "name": "Coder With Handoff",
            "role": "coder",
            "default_model_id": "model-1",
            "allow_handoff": True,
        })
        agent_id = create.json()["data"]["id"]
        resp = client.get(f"/api/v1/agents/{agent_id}")
        body = resp.json()["data"]
        assert "handoff_policy" in body
        assert body["handoff_policy"]["can_initiate"] is True
        assert body["handoff_policy"]["on_provider_error"] == "retry_once"

    def test_get_station_returns_handoff_policy(self, client):
        create = client.post("/api/v1/agents", json={
            "name": "Reviewed Agent",
            "role": "reviewer",
            "default_model_id": "model-1",
            "allow_handoff": True,
        })
        agent_id = create.json()["data"]["id"]
        resp = client.get(f"/api/v1/agents/{agent_id}")
        body = resp.json()["data"]
        assert "handoff_policy" in body
        # Policy is a real dict, not a string
        assert isinstance(body["handoff_policy"], dict)
        assert "can_initiate" in body["handoff_policy"]

    def test_legacy_row_without_handoff_policy_falls_back(self, db_session):
        """Rows seeded before V1.0-3 lack handoff_policy; the read path
        should synthesise a default from the boolean allow_handoff column.
        """
        from src.models.agent import AgentStation
        station = AgentStation(
            id="legacy-test",
            name="Legacy",
            role="coder",
            default_model_id="model-1",
            system_prompt="",
            allow_handoff=True,
            is_enabled=True,
            handoff_policy=None,  # simulate a pre-migration row
        )
        policy = station.get_handoff_policy()
        assert policy["can_initiate"] is True
        assert policy["on_provider_error"] == "retry_once"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def seed_builtin_station(db_session):
    """Create a built-in station (bypasses the normal API which forces
    is_builtin=False). Returns the AgentStation object."""
    from src.models.agent import AgentStation
    def _make(slug: str, role: str = "planner"):
        station = AgentStation(
            id=f"test-builtin-{slug}",
            name=f"Test Builtin {slug}",
            role=role,
            default_model_id="model-1",
            system_prompt="test",
            allow_handoff=False,
            is_enabled=True,
            is_builtin=True,
            slug=slug,
        )
        station.set_handoff_policy({
            "can_initiate": False,
            "on_quota_exhausted": "fallback_backup",
            "on_provider_error": "retry_once",
        })
        db_session.add(station)
        db_session.commit()
        db_session.refresh(station)
        return station
    return _make

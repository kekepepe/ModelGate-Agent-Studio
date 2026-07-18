from scripts.live_provider_acceptance import Api, SCENARIOS, seed_workspace


def test_live_acceptance_suite_defines_all_six_strict_modes():
    assert [scenario.key for scenario in SCENARIOS] == [
        "A-direct",
        "B-single",
        "C-coder-verifier",
        "D-research-coder-verifier",
        "E-parallel",
        "F-replan-handoff",
    ]
    assert SCENARIOS[0].expected_modes == ("direct",)
    assert SCENARIOS[4].expected_modes == ("parallel_multi_agent",)
    assert SCENARIOS[5].replan_and_handoff is True


def test_acceptance_fixture_is_isolated_clean_and_parallel_scope_aligned(tmp_path):
    workspace = tmp_path / "acceptance"
    initial_sha = seed_workspace(workspace)
    assert len(initial_sha) == 40
    assert (workspace / "backend" / "math_utils.py").exists()
    assert "backend.math_utils" in (workspace / "tests" / "test_math_utils.py").read_text()
    assert not (workspace / "math_utils.py").exists()


def test_api_splits_origin_from_versioned_root():
    api = Api("https://provider-gate.example/api/v1/", 1)
    try:
        assert api.origin == "https://provider-gate.example"
        assert api.api_root == "https://provider-gate.example/api/v1"
    finally:
        api.close()

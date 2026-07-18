import pytest

from scripts.rag_eval import run_evaluation


@pytest.mark.slow
def test_fixed_rag_evaluation_meets_quality_security_and_latency_baseline():
    metrics = run_evaluation()["metrics"]
    assert metrics["question_count"] == 30
    assert metrics["recall_at_5"] >= 0.90
    assert metrics["mrr"] >= 0.80
    assert metrics["ndcg_at_5"] >= 0.85
    assert metrics["empty_result_accuracy"] >= 0.80
    assert metrics["forbidden_scope_retrieval_rate"] == 0
    assert metrics["disabled_knowledge_retrieval_rate"] == 0
    assert metrics["latency_p95_ms"] < 500

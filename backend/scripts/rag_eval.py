"""Run the fixed 30-question RAG quality and latency baseline."""

from __future__ import annotations

import argparse
import json
import math
import os
import statistics
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("EXECUTION_MODE", "mock")

from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from src.core.config import settings  # noqa: E402
from src.core.database import Base  # noqa: E402
from src.models import agent as _agent  # noqa: E402,F401
from src.models import handoff as _handoff  # noqa: E402,F401
from src.models import knowledge as _knowledge  # noqa: E402,F401
from src.models import model as _model  # noqa: E402,F401
from src.models import quota as _quota  # noqa: E402,F401
from src.models import selection as _selection  # noqa: E402,F401
from src.models import supervisor as _supervisor  # noqa: E402,F401
from src.models import tool as _tool  # noqa: E402,F401
from src.models import workspace as _workspace  # noqa: E402,F401
from src.services import knowledge_source_service, retrieval_service  # noqa: E402
from src.services.embedding_service import (  # noqa: E402
    EmbeddingAdapter,
    LocalHashEmbeddingAdapter,
    RealEmbeddingProviderAdapter,
)


ROOT = BACKEND_ROOT
DATASET_PATH = ROOT / "evals" / "rag_dataset.json"
CORPUS_ROOT = ROOT / "evals" / "corpus"


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, math.ceil(percentile * len(ordered)) - 1)
    return round(ordered[index], 3)


def run_evaluation(embedding_adapter: EmbeddingAdapter | None = None) -> dict:
    dataset = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    adapter = embedding_adapter or LocalHashEmbeddingAdapter()
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    previous_workspace_root = settings.workspace_root
    settings.workspace_root = str(CORPUS_ROOT)
    try:
        source_ids = {}
        for name, scope in (("public", "public/**"), ("private", "private/**"), ("disabled", "public/**")):
            source = knowledge_source_service.create_source(
                db,
                name=f"RAG eval {name}",
                source_type="workspace",
                uri=str(CORPUS_ROOT / name),
                workspace_scope=scope,
            )
            source_ids[name] = source["id"]
            knowledge_source_service.sync_source(
                db, source["id"], embedding_adapter=adapter,
            )
        knowledge_source_service.set_source_status(db, source_ids["disabled"], "disabled")

        recall_hits = 0
        reciprocal_ranks = []
        ndcg_scores = []
        precisions = []
        empty_hits = 0
        empty_total = 0
        forbidden_retrieved = 0
        disabled_retrieved = 0
        used_ratios = []
        latencies = []
        scan_counts = []
        results = []
        for item in dataset:
            result = retrieval_service.retrieve(
                db,
                query=item["query"],
                workspace_scope=item.get("scope"),
                token_budget=600,
                limit=5,
                embedding_adapter=adapter,
            )
            paths = [candidate["path"] for candidate in result["items"]]
            expected = item.get("expected_path")
            rank = paths.index(expected) + 1 if expected in paths else None
            if expected:
                recall_hits += int(rank is not None and rank <= 5)
                reciprocal_ranks.append(1 / rank if rank else 0.0)
                ndcg_scores.append(1 / math.log2(rank + 1) if rank else 0.0)
                precisions.append(1 / max(1, len(paths)) if rank else 0.0)
            if item.get("should_empty"):
                empty_total += 1
                empty_hits += int(not paths)
            if item.get("forbidden") and any(path.startswith("private/") for path in paths):
                forbidden_retrieved += 1
            if item.get("disabled") and any(path.startswith("disabled/") for path in paths):
                disabled_retrieved += 1
            used_ratios.append(result["token_count"] / max(1, result["token_budget"]))
            latencies.append(float(result["latency_ms"]))
            scan_counts.append(result["candidate_scan_count"])
            results.append({
                "id": item["id"], "paths": paths, "rank": rank,
                "scores": [candidate["score"] for candidate in result["items"]],
                "latency_ms": result["latency_ms"],
                "candidate_scan_count": result["candidate_scan_count"],
            })

        labelled = sum(1 for item in dataset if item.get("expected_path"))
        metrics = {
            "question_count": len(dataset),
            "recall_at_5": round(recall_hits / max(1, labelled), 4),
            "precision_at_5": round(statistics.mean(precisions), 4),
            "mrr": round(statistics.mean(reciprocal_ranks), 4),
            "ndcg_at_5": round(statistics.mean(ndcg_scores), 4),
            "empty_result_accuracy": round(empty_hits / max(1, empty_total), 4),
            "forbidden_scope_retrieval_rate": round(forbidden_retrieved / max(1, sum(bool(i.get("forbidden")) for i in dataset)), 4),
            "disabled_knowledge_retrieval_rate": round(disabled_retrieved / max(1, sum(bool(i.get("disabled")) for i in dataset)), 4),
            "context_used_ratio": round(statistics.mean(used_ratios), 4),
            "latency_p50_ms": _percentile(latencies, 0.50),
            "latency_p95_ms": _percentile(latencies, 0.95),
            "candidate_scan_p95": _percentile([float(value) for value in scan_counts], 0.95),
        }
        return {
            "embedding": {
                "adapter": adapter.name,
                "model": adapter.model_name,
                "version": adapter.version,
                "fingerprint": adapter.fingerprint,
                "dimensions": getattr(adapter, "dimensions", 64),
                "fallback_reason": adapter.fallback_reason,
            },
            "metrics": metrics,
            "results": results,
        }
    finally:
        settings.workspace_root = previous_workspace_root
        db.close()
        engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--embedding-backend", choices=("local_hash", "real"), default="local_hash",
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--enforce-thresholds", action="store_true")
    args = parser.parse_args()
    adapter: EmbeddingAdapter
    if args.embedding_backend == "real":
        # Strict evaluation deliberately avoids ResilientEmbeddingAdapter: a
        # Provider failure must fail this gate, never turn into a LocalHash pass.
        adapter = RealEmbeddingProviderAdapter()
    else:
        adapter = LocalHashEmbeddingAdapter()
    report = run_evaluation(adapter)
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    sys.stdout.write(rendered + "\n")
    if args.enforce_thresholds:
        metrics = report["metrics"]
        passed = (
            metrics["question_count"] == 30
            and metrics["recall_at_5"] >= 0.90
            and metrics["mrr"] >= 0.80
            and metrics["ndcg_at_5"] >= 0.85
            and metrics["empty_result_accuracy"] >= 0.80
            and metrics["forbidden_scope_retrieval_rate"] == 0
            and metrics["disabled_knowledge_retrieval_rate"] == 0
            and metrics["latency_p95_ms"] < 500
        )
        if not passed:
            raise SystemExit(1)


if __name__ == "__main__":
    main()

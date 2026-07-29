"""
Shared harness: seed memories -> ask questions -> collect answers -> hand off to a judge.

Each suite provides a small JSON/JSONL dataset and a suite-specific driver
(see suites/*/run.py) that calls into this harness rather than reimplementing
seed/query/score plumbing.
"""
from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable

from memclaw_client import MemclawClient

RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"


@dataclass
class QAResult:
    question_id: str
    question: str
    reference_answer: str
    condition: str  # e.g. "memclaw", "full_context", "no_memory", "agent_scoped_only"
    answer: str
    latency_ms: float
    judged_correct: bool | None = None
    judge_notes: str | None = None


def seed_memories(client: MemclawClient, memories: list[str], visibility: str = "scope_team") -> list[str]:
    """Write each memory string, return the memory ids memclaw assigns."""
    ids = []
    for m in memories:
        resp = client.write(m, visibility=visibility)
        mem_id = resp.get("id") or resp.get("memory_id")
        if mem_id:
            ids.append(mem_id)
    return ids


def ask(client: MemclawClient, question: str, answer_fn: Callable[[dict], str],
        top_k: int = 5) -> tuple[str, float]:
    """Recall for `question`, then let `answer_fn` turn the recall payload into a final answer
    (e.g. by feeding it to an LLM as context). Returns (answer, latency_ms)."""
    start = time.perf_counter()
    recall_payload = client.recall(question, top_k=top_k, include_brief=True)
    answer = answer_fn(recall_payload)
    latency_ms = (time.perf_counter() - start) * 1000
    return answer, latency_ms


def run_suite(suite_name: str, qa_items: list[dict[str, Any]], condition: str,
              client: MemclawClient, answer_fn: Callable[[dict], str],
              judge_fn: Callable[[str, str, str], tuple[bool, str]] | None = None) -> Path:
    """
    qa_items: [{"id": ..., "question": ..., "reference_answer": ...}, ...]
    judge_fn(question, reference_answer, answer) -> (is_correct, notes)
    Writes results/<run_id>.json and returns its path.
    """
    results: list[QAResult] = []
    for item in qa_items:
        answer, latency_ms = ask(client, item["question"], answer_fn)
        judged_correct, notes = (None, None)
        if judge_fn:
            judged_correct, notes = judge_fn(item["question"], item["reference_answer"], answer)
        results.append(QAResult(
            question_id=item["id"],
            question=item["question"],
            reference_answer=item["reference_answer"],
            condition=condition,
            answer=answer,
            latency_ms=latency_ms,
            judged_correct=judged_correct,
            judge_notes=notes,
        ))

    run_id = f"{suite_name}_{condition}_{uuid.uuid4().hex[:8]}"
    out_path = RESULTS_DIR / f"{run_id}.json"
    RESULTS_DIR.mkdir(exist_ok=True)

    scored = [r for r in results if r.judged_correct is not None]
    accuracy = sum(1 for r in scored if r.judged_correct) / len(scored) if scored else None
    avg_latency = sum(r.latency_ms for r in results) / len(results) if results else 0.0

    payload = {
        "run_id": run_id,
        "suite": suite_name,
        "condition": condition,
        "accuracy": accuracy,
        "avg_latency_ms": avg_latency,
        "n": len(results),
        "results": [asdict(r) for r in results],
    }
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return out_path


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]

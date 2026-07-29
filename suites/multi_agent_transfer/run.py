"""
Track B suite 2: multi-agent knowledge transfer.

Agent A writes a fact at scope_team. Agent B -- a distinct agent identity in
the same fleet, with no shared conversation history -- is then asked a
question that requires that fact, using ONLY memclaw_recall (no seeding).
Baseline: Agent B in a *different* fleet (or with agent-scoped-only recall),
which should NOT find the fact -- simulating a single-agent memory tool where
knowledge doesn't cross agents.

Usage:
    python suites/multi_agent_transfer/run.py --fleet-id <your-fleet-id>
"""
from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "runners"))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from memclaw_client import MemclawClient
from judges.llm_judge import judge

DATA_PATH = Path(__file__).resolve().parents[2] / "datasets" / "custom" / "multi_agent_transfer.json"
RESULTS_DIR = Path(__file__).resolve().parents[2] / "results"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fleet-id", required=True, help="Shared fleet for Agent A and Agent B")
    args = ap.parse_args()

    scenarios = json.loads(DATA_PATH.read_text(encoding="utf-8"))["scenarios"]
    run_id = uuid.uuid4().hex[:6]

    results = []
    for s in scenarios:
        agent_a = MemclawClient(agent_id=f"bench-transfer-a-{run_id}", fleet_id=args.fleet_id)
        agent_b_same_fleet = MemclawClient(agent_id=f"bench-transfer-b-{run_id}", fleet_id=args.fleet_id)
        agent_b_isolated = MemclawClient(agent_id=f"bench-transfer-b-iso-{run_id}")  # no fleet_id, no seed

        agent_a.write(s["fact"], visibility="scope_team")

        recall_shared = agent_b_same_fleet.recall(s["question"], include_brief=True)
        answer_shared = recall_shared.get("brief", {}).get("summary", "") or " ".join(
            m.get("content", "") for m in recall_shared.get("results", [])[:3])
        correct_shared, notes_shared = judge(s["question"], s["reference_answer"], answer_shared)

        recall_isolated = agent_b_isolated.recall(s["question"], include_brief=True)
        answer_isolated = recall_isolated.get("brief", {}).get("summary", "") or " ".join(
            m.get("content", "") for m in recall_isolated.get("results", [])[:3])
        correct_isolated, notes_isolated = judge(s["question"], s["reference_answer"], answer_isolated)

        results.append({
            "scenario_id": s["id"],
            "same_fleet_correct": correct_shared,
            "same_fleet_answer": answer_shared,
            "isolated_agent_correct": correct_isolated,
            "isolated_agent_answer": answer_isolated,
        })

    same_fleet_rate = sum(r["same_fleet_correct"] for r in results) / len(results)
    isolated_rate = sum(r["isolated_agent_correct"] for r in results) / len(results)

    RESULTS_DIR.mkdir(exist_ok=True)
    out_path = RESULTS_DIR / f"multi_agent_transfer_{run_id}.json"
    out_path.write_text(json.dumps({
        "suite": "multi_agent_transfer",
        "same_fleet_accuracy": same_fleet_rate,
        "isolated_agent_accuracy": isolated_rate,
        "n": len(results),
        "results": results,
    }, indent=2), encoding="utf-8")
    print(f"same-fleet transfer accuracy: {same_fleet_rate:.0%}, isolated-agent baseline: {isolated_rate:.0%}")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()

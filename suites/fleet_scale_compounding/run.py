"""
Track B suite 5: fleet-scale compounding.

N agents each write a subset of the shared facts (simulating a fleet that has
been contributing knowledge over time). A late-joining agent, with zero
history of its own, then answers questions using only memclaw_recall.
Baseline: an agent with the same questions but only its OWN (empty) history --
i.e. what a single-agent memory tool would give a new agent.

Usage:
    python suites/fleet_scale_compounding/run.py --fleet-id <your-fleet-id> --n-agents 4
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

DATA_PATH = Path(__file__).resolve().parents[2] / "datasets" / "custom" / "fleet_scale_compounding.json"
RESULTS_DIR = Path(__file__).resolve().parents[2] / "results"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fleet-id", required=True)
    ap.add_argument("--n-agents", type=int, default=4, help="Number of contributing agents")
    args = ap.parse_args()

    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    facts, questions = data["shared_facts"], data["questions"]
    run_id = uuid.uuid4().hex[:6]

    contributors = [MemclawClient(agent_id=f"bench-fleet-{i}-{run_id}", fleet_id=args.fleet_id)
                     for i in range(args.n_agents)]
    for i, fact in enumerate(facts):
        contributors[i % args.n_agents].write(fact, visibility="scope_team")

    late_joiner = MemclawClient(agent_id=f"bench-fleet-latejoin-{run_id}", fleet_id=args.fleet_id)
    isolated_new_agent = MemclawClient(agent_id=f"bench-fleet-isolated-{run_id}")  # no fleet, no history

    results = []
    for q in questions:
        recall_fleet = late_joiner.recall(q["question"], include_brief=True)
        answer_fleet = recall_fleet.get("brief", {}).get("summary", "") or " ".join(
            m.get("content", "") for m in recall_fleet.get("results", [])[:3])
        correct_fleet, _ = judge(q["question"], q["reference_answer"], answer_fleet)

        recall_isolated = isolated_new_agent.recall(q["question"], include_brief=True)
        answer_isolated = recall_isolated.get("brief", {}).get("summary", "") or " ".join(
            m.get("content", "") for m in recall_isolated.get("results", [])[:3])
        correct_isolated, _ = judge(q["question"], q["reference_answer"], answer_isolated)

        results.append({"question_id": q["id"], "late_joiner_correct": correct_fleet,
                         "isolated_new_agent_correct": correct_isolated})

    fleet_rate = sum(r["late_joiner_correct"] for r in results) / len(results)
    isolated_rate = sum(r["isolated_new_agent_correct"] for r in results) / len(results)

    RESULTS_DIR.mkdir(exist_ok=True)
    out_path = RESULTS_DIR / f"fleet_scale_compounding_{run_id}.json"
    out_path.write_text(json.dumps({
        "suite": "fleet_scale_compounding",
        "n_agents": args.n_agents,
        "late_joiner_accuracy": fleet_rate,
        "isolated_new_agent_accuracy": isolated_rate,
        "n_questions": len(results),
        "results": results,
    }, indent=2), encoding="utf-8")
    print(f"late-joiner (fleet knowledge) accuracy: {fleet_rate:.0%}, isolated new agent: {isolated_rate:.0%}")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()

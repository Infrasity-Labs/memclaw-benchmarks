"""
Track B suite 4: contradiction detection & convergence.

Agent A writes a stale fact. Agent B (same fleet) writes a conflicting
correction and transitions the stale memory to status=outdated. A third
agent, C, then recalls the question and should converge on the corrected
fact. Also checks memclaw_insights(focus="contradictions") flags the
conflict before it's resolved.

Usage:
    python suites/contradiction_convergence/run.py --fleet-id <your-fleet-id>
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

DATA_PATH = Path(__file__).resolve().parents[2] / "datasets" / "custom" / "contradiction_convergence.json"
RESULTS_DIR = Path(__file__).resolve().parents[2] / "results"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fleet-id", required=True)
    args = ap.parse_args()

    scenarios = json.loads(DATA_PATH.read_text(encoding="utf-8"))["scenarios"]
    run_id = uuid.uuid4().hex[:6]

    results = []
    for s in scenarios:
        agent_a = MemclawClient(agent_id=f"bench-conv-a-{run_id}", fleet_id=args.fleet_id)
        agent_b = MemclawClient(agent_id=f"bench-conv-b-{run_id}", fleet_id=args.fleet_id)
        agent_c = MemclawClient(agent_id=f"bench-conv-c-{run_id}", fleet_id=args.fleet_id)

        stale = agent_a.write(s["stale_fact"], visibility="scope_team")
        stale_id = stale.get("id") or stale.get("memory_id")

        # Give the background contradiction-detection pass a moment, then check insights flagged it.
        insights = agent_b.insights(focus="contradictions", scope="fleet")
        flagged = bool(insights.get("results") or insights.get("count", 0))

        agent_b.write(s["correction"], visibility="scope_team")
        if stale_id:
            agent_b.manage_transition(stale_id, status="outdated")

        recall = agent_c.recall(s["question"], include_brief=True)
        answer = recall.get("brief", {}).get("summary", "") or " ".join(
            m.get("content", "") for m in recall.get("results", [])[:3])
        converged, notes = judge(s["question"], s["reference_answer"], answer)

        results.append({
            "scenario_id": s["id"],
            "contradiction_flagged": flagged,
            "converged_to_correction": converged,
            "agent_c_answer": answer,
        })

    flag_rate = sum(r["contradiction_flagged"] for r in results) / len(results)
    convergence_rate = sum(r["converged_to_correction"] for r in results) / len(results)

    RESULTS_DIR.mkdir(exist_ok=True)
    out_path = RESULTS_DIR / f"contradiction_convergence_{run_id}.json"
    out_path.write_text(json.dumps({
        "suite": "contradiction_convergence",
        "contradiction_flag_rate": flag_rate,
        "convergence_rate": convergence_rate,
        "n": len(results),
        "results": results,
    }, indent=2), encoding="utf-8")
    print(f"contradiction flag rate: {flag_rate:.0%}, convergence rate: {convergence_rate:.0%}")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()

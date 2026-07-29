"""
Track B suite 3: trust-tier access-control correctness.

Pass/fail security suite, not an accuracy score. Asserts the trust-tier rules
documented in the memclaw skill (memclaw_keystones §6):
  trust 1 -- read own fleet only, write own fleet only
  trust 2 -- read cross-fleet, write own fleet only
  trust 3 -- read/write all, including deletes

Requires three pre-provisioned agent credentials at trust 1/2/3 respectively
(trust is granted by an operator, not self-assignable -- see MEMCLAW_TRUST1_*,
MEMCLAW_TRUST2_*, MEMCLAW_TRUST3_* env vars below).

Usage:
    python suites/trust_tier_access/run.py
"""
from __future__ import annotations

import json
import os
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "runners"))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from memclaw_client import MemclawClient
from judges.assertions import (
    assert_delete_allowed,
    assert_delete_denied,
    assert_read_allowed,
    assert_read_denied,
)

RESULTS_DIR = Path(__file__).resolve().parents[2] / "results"


def client_for(env_prefix: str) -> MemclawClient | None:
    agent_id = os.environ.get(f"{env_prefix}_AGENT_ID")
    api_key = os.environ.get(f"{env_prefix}_API_KEY")
    if not agent_id or not api_key:
        return None
    return MemclawClient(agent_id=agent_id, api_key=api_key)


def main():
    trust1 = client_for("MEMCLAW_TRUST1")
    trust2 = client_for("MEMCLAW_TRUST2")
    trust3 = client_for("MEMCLAW_TRUST3")
    missing = [name for name, c in [("trust1", trust1), ("trust2", trust2), ("trust3", trust3)] if c is None]
    if missing:
        print(f"Missing credentials for: {missing}. Set MEMCLAW_TRUST{{1,2,3}}_AGENT_ID / _API_KEY.")
        sys.exit(1)

    checks = []
    checks.append(("trust1_fleet_read_denied", assert_read_denied(trust1, scope="fleet")))
    checks.append(("trust1_all_read_denied", assert_read_denied(trust1, scope="all")))
    checks.append(("trust2_fleet_read_allowed", assert_read_allowed(trust2, scope="fleet")))
    checks.append(("trust2_all_read_allowed", assert_read_allowed(trust2, scope="all")))

    # Seed a throwaway memory as trust3 to test delete permissions on.
    probe = trust3.write(f"trust-tier-access probe {uuid.uuid4().hex[:8]}", visibility="scope_agent")
    probe_id = probe.get("id") or probe.get("memory_id")
    if probe_id:
        checks.append(("trust1_delete_denied", assert_delete_denied(trust1, probe_id)))
        checks.append(("trust3_delete_allowed", assert_delete_allowed(trust3, probe_id)))

    n_passed = sum(1 for _, r in checks if r.passed)
    RESULTS_DIR.mkdir(exist_ok=True)
    out_path = RESULTS_DIR / f"trust_tier_access_{uuid.uuid4().hex[:8]}.json"
    out_path.write_text(json.dumps({
        "suite": "trust_tier_access",
        "pass_rate": n_passed / len(checks),
        "n": len(checks),
        "checks": [{"name": name, "passed": r.passed, "detail": r.detail} for name, r in checks],
    }, indent=2), encoding="utf-8")
    print(f"trust-tier access: {n_passed}/{len(checks)} checks passed")
    for name, r in checks:
        print(f"  [{'PASS' if r.passed else 'FAIL'}] {name}: {r.detail}")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()

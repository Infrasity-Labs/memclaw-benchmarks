"""
Thin HTTP client over the memclaw REST API, mirroring the memclaw_* MCP tools.

The MCP tool schemas (memclaw_recall, memclaw_write, memclaw_manage, ...) are
confirmed against the live MCP server this repo was built alongside. The exact
REST paths below are our best-effort mapping of those same operations and are
NOT independently confirmed — verify/adjust MEMCLAW_*_PATH env vars against
your deployment's REST docs (memclaw.net) before trusting benchmark numbers.

Auth: set MEMCLAW_API_KEY (Bearer token) and MEMCLAW_BASE_URL.
Identity: every call requires agent_id; fleet_id is optional (server resolves
home fleet when omitted, per the memclaw skill).
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

import requests

BASE_URL = os.environ.get("MEMCLAW_BASE_URL", "https://memclaw.net")
API_KEY = os.environ.get("MEMCLAW_API_KEY")

# Best-effort REST path mapping -- override via env if your deployment differs.
PATHS = {
    "recall": os.environ.get("MEMCLAW_RECALL_PATH", "/api/v1/memory/recall"),
    "write": os.environ.get("MEMCLAW_WRITE_PATH", "/api/v1/memory/write"),
    "manage": os.environ.get("MEMCLAW_MANAGE_PATH", "/api/v1/memory/manage"),
    "list": os.environ.get("MEMCLAW_LIST_PATH", "/api/v1/memory/list"),
    "evolve": os.environ.get("MEMCLAW_EVOLVE_PATH", "/api/v1/memory/evolve"),
    "insights": os.environ.get("MEMCLAW_INSIGHTS_PATH", "/api/v1/memory/insights"),
    "keystones": os.environ.get("MEMCLAW_KEYSTONES_PATH", "/api/v1/keystones"),
    "keystones_set": os.environ.get("MEMCLAW_KEYSTONES_SET_PATH", "/api/v1/keystones"),
    "doc": os.environ.get("MEMCLAW_DOC_PATH", "/api/v1/doc"),
}


class MemclawError(RuntimeError):
    def __init__(self, status: int, payload: Any):
        super().__init__(f"memclaw request failed ({status}): {payload}")
        self.status = status
        self.payload = payload


@dataclass
class MemclawClient:
    """Call as a specific agent identity. One client per (agent_id, fleet_id) pair."""

    agent_id: str
    fleet_id: str | None = None
    base_url: str = BASE_URL
    api_key: str | None = field(default=API_KEY)
    session: requests.Session = field(default_factory=requests.Session)

    def _headers(self) -> dict[str, str]:
        if not self.api_key:
            raise RuntimeError("MEMCLAW_API_KEY is not set")
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    def _post(self, path_key: str, body: dict[str, Any]) -> dict[str, Any]:
        url = self.base_url.rstrip("/") + PATHS[path_key]
        resp = self.session.post(url, json=body, headers=self._headers(), timeout=60)
        if resp.status_code >= 400:
            raise MemclawError(resp.status_code, resp.text)
        return resp.json()

    def write(self, content: str, visibility: str = "scope_team", write_mode: str = "auto") -> dict:
        body = {"agent_id": self.agent_id, "content": content, "visibility": visibility, "write_mode": write_mode}
        if self.fleet_id:
            body["fleet_id"] = self.fleet_id
        return self._post("write", body)

    def recall(self, query: str, top_k: int = 5, include_brief: bool = False,
               scope: str | None = None) -> dict:
        body = {"agent_id": self.agent_id, "query": query, "top_k": top_k, "include_brief": include_brief}
        if scope:
            body["scope"] = scope
        return self._post("recall", body)

    def manage_transition(self, memory_id: str, status: str) -> dict:
        return self._post("manage", {"agent_id": self.agent_id, "op": "transition",
                                      "id": memory_id, "status": status})

    def manage_read(self, memory_id: str) -> dict:
        return self._post("manage", {"agent_id": self.agent_id, "op": "read", "id": memory_id})

    def manage_delete(self, memory_id: str) -> dict:
        return self._post("manage", {"agent_id": self.agent_id, "op": "delete", "id": memory_id})

    def evolve(self, outcome: str, outcome_type: str, related_ids: list[str],
               scope: str = "agent") -> dict:
        body = {"agent_id": self.agent_id, "outcome": outcome, "outcome_type": outcome_type,
                "related_ids": related_ids, "scope": scope}
        if self.fleet_id and scope == "fleet":
            body["fleet_id"] = self.fleet_id
        return self._post("evolve", body)

    def insights(self, focus: str, scope: str = "agent") -> dict:
        return self._post("insights", {"agent_id": self.agent_id, "focus": focus, "scope": scope})

    def keystones(self) -> dict:
        return self._post("keystones", {"agent_id": self.agent_id, "fleet_id": self.fleet_id})

    def keystones_set(self, op: str, title: str, content: str, weight: str,
                       scope: str = "agent") -> dict:
        body = {"agent_id": self.agent_id, "op": op, "scope": scope, "title": title,
                "content": content, "weight": weight}
        if self.fleet_id:
            body["fleet_id"] = self.fleet_id
        return self._post("keystones_set", body)

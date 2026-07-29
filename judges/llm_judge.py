"""
LLM-judge scoring for Track A (recall accuracy) and the contradiction-convergence
suite. Same methodology mem0's benchmark uses: an LLM compares a candidate answer
to a reference answer and returns a correct/incorrect verdict, tolerant of
paraphrasing.

Requires ANTHROPIC_API_KEY. Uses the Messages API directly (see the claude-api
skill for current model ids/params if you need to change the model).
"""
from __future__ import annotations

import json
import os

import anthropic

JUDGE_MODEL = os.environ.get("MEMCLAW_JUDGE_MODEL", "claude-sonnet-5")

JUDGE_PROMPT = """You are grading whether a candidate answer correctly conveys the same \
information as a reference answer. Minor phrasing differences are fine; the \
candidate must not omit or contradict the key fact(s) in the reference.

Question: {question}
Reference answer: {reference}
Candidate answer: {candidate}

Respond with strict JSON: {{"correct": true|false, "notes": "<one sentence>"}}"""


def judge(question: str, reference_answer: str, candidate_answer: str) -> tuple[bool, str]:
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model=JUDGE_MODEL,
        max_tokens=200,
        messages=[{
            "role": "user",
            "content": JUDGE_PROMPT.format(
                question=question, reference=reference_answer, candidate=candidate_answer,
            ),
        }],
    )
    text = msg.content[0].text.strip()
    try:
        parsed = json.loads(text)
        return bool(parsed["correct"]), parsed.get("notes", "")
    except (json.JSONDecodeError, KeyError):
        # Judge didn't return clean JSON -- treat as ungraded rather than silently wrong.
        return False, f"judge parse failure: {text[:200]}"

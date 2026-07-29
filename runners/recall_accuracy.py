"""Shared driver for the Track A recall-accuracy suites (LOCOMO, LongMemEval).
Both datasets are normalized to the same conversation/qa JSONL shape (see each
dataset's README), so one driver serves both -- suites/*/run.py just pick the
DATA_DIR and suite name.
"""
from __future__ import annotations

import argparse
import sys
import uuid
from pathlib import Path

import anthropic

from harness import load_jsonl, run_suite, seed_memories
from memclaw_client import MemclawClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from judges.llm_judge import judge, JUDGE_MODEL


def make_answer_fn_memclaw():
    client = anthropic.Anthropic()

    def answer_fn(recall_payload: dict) -> str:
        brief = recall_payload.get("brief", {}).get("summary", "")
        top_hits = "\n".join(m.get("content", "") for m in recall_payload.get("results", [])[:5])
        prompt = (f"Context from memory:\n{brief}\n\nRelevant memories:\n{top_hits}\n\n"
                  "Answer the question concisely using only this context.")
        msg = client.messages.create(model=JUDGE_MODEL, max_tokens=200,
                                      messages=[{"role": "user", "content": prompt}])
        return msg.content[0].text.strip()
    return answer_fn


def run(suite_name: str, data_dir: Path, conversation_file: str, condition: str, limit: int) -> None:
    conv_path = data_dir / conversation_file
    qa_path = data_dir / conversation_file.replace("conversation", "qa")
    if not conv_path.exists() or not qa_path.exists():
        print(f"Missing dataset files under {data_dir} -- see {data_dir / 'README.md'}")
        sys.exit(1)

    turns = load_jsonl(conv_path)
    qa_items = load_jsonl(qa_path)[:limit]
    anthropic_client = anthropic.Anthropic()

    if condition == "memclaw":
        agent_id = f"bench-{suite_name}-{uuid.uuid4().hex[:6]}"
        client = MemclawClient(agent_id=agent_id)
        seed_memories(client, [t["text"] for t in turns])
        out = run_suite(suite_name, qa_items, "memclaw", client, make_answer_fn_memclaw(), judge)
        print(f"Wrote {out}")
        return

    if condition == "full_context":
        conv_text = "\n".join(t["text"] for t in turns)
        prompt_fn = lambda q: f"Conversation:\n{conv_text}\n\nQuestion: {q}\nAnswer concisely."
    else:  # no_memory
        prompt_fn = lambda q: q

    correct_count = 0
    for item in qa_items:
        msg = anthropic_client.messages.create(
            model=JUDGE_MODEL, max_tokens=200,
            messages=[{"role": "user", "content": prompt_fn(item["question"])}])
        answer = msg.content[0].text.strip()
        is_correct, _notes = judge(item["question"], item["reference_answer"], answer)
        correct_count += int(is_correct)
    print(f"{condition} accuracy: {correct_count}/{len(qa_items)}")


def cli(suite_name: str, data_dir: Path) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--condition", choices=["memclaw", "full_context", "no_memory"], default="memclaw")
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--conversation-file", default="conversation_001.jsonl")
    args = ap.parse_args()
    run(suite_name, data_dir, args.conversation_file, args.condition, args.limit)

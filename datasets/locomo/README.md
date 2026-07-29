# LOCOMO dataset

Populate this directory from the public LOCOMO release
(https://github.com/snap-research/locomo — verify current location before
fetching; the dataset has moved before).

Expected format, one file pair per conversation:

`conversation_001.jsonl` — one turn per line:
```json
{"speaker": "Alice", "text": "...", "session": 1, "timestamp": "..."}
```

`qa_001.jsonl` — one question per line:
```json
{"id": "q1", "question": "...", "reference_answer": "...", "category": "single-hop"}
```

A `scripts/fetch_locomo.py` converter (not yet written) should map the
original LOCOMO release format into these two flat JSONL shapes so
`suites/recall_accuracy_locomo/run.py` can consume them unmodified.

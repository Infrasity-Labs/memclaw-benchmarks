# LongMemEval dataset

Populate from the public LongMemEval release
(https://github.com/xiaowu0162/LongMemEval — verify current location before
fetching). Same target format as `datasets/locomo/` (`conversation_*.jsonl` +
`qa_*.jsonl`) so it runs through the same harness — see
`suites/recall_accuracy_longmemeval/run.py`, which mirrors
`suites/recall_accuracy_locomo/run.py` with a different DATA_DIR.

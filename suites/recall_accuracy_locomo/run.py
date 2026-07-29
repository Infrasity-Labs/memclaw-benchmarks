"""
Track A: LOCOMO recall accuracy.

Usage:
    python suites/recall_accuracy_locomo/run.py --condition memclaw --limit 20
    python suites/recall_accuracy_locomo/run.py --condition full_context --limit 20
    python suites/recall_accuracy_locomo/run.py --condition no_memory --limit 20

Dataset: datasets/locomo/*.jsonl -- see datasets/locomo/README.md.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "runners"))
from recall_accuracy import cli

DATA_DIR = Path(__file__).resolve().parents[2] / "datasets" / "locomo"

if __name__ == "__main__":
    cli("recall_accuracy_locomo", DATA_DIR)

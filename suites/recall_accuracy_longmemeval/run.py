"""
Track A: LongMemEval recall accuracy. Mirrors recall_accuracy_locomo/run.py --
see runners/recall_accuracy.py for the shared driver.

Usage:
    python suites/recall_accuracy_longmemeval/run.py --condition memclaw --limit 20
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "runners"))
from recall_accuracy import cli

DATA_DIR = Path(__file__).resolve().parents[2] / "datasets" / "longmemeval"

if __name__ == "__main__":
    cli("recall_accuracy_longmemeval", DATA_DIR)

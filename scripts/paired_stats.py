"""Paired significance tests for MemoryArena formal-reasoning arms.

Same method used for the math/phys gpt-4.1 comparisons:
  - progress score: paired bootstrap CI + sign-flip permutation test (20k)
  - paper passrate: McNemar exact (final-subtask definition, per eval.py)
  - subtask correctness: McNemar exact over aligned subtasks

Computed directly from per-paper result.jsonl logs.
"""
import json
import os
import sys
from math import comb

import numpy as np

RNG = np.random.default_rng(20260809)
N_BOOT = 20000
N_PERM = 20000


def load_arm(root):
    """{paper: [is_correct, ...]} for every paper with a result.jsonl."""
    out = {}
    for paper in sorted(os.listdir(root)):
        path = os.path.join(root, paper, "result.jsonl")
        if not os.path.isfile(path):
            continue
        with open(path, "r", encoding="utf-8") as f:
            logs = [json.loads(line) for line in f if line.strip()]
        if logs:
            out[paper] = [bool(log["is_correct"]) for log in logs]
    return out


def mcnemar_exact(b, c):
    """Two-sided exact binomial p for discordant counts b, c."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = sum(comb(n, i) for i in range(k + 1)) / (2 ** n)
    return min(1.0, 2 * tail)


def compare(name_a, arm_a, name_b, arm_b):
    papers = sorted(set(arm_a) & set(arm_b))
    print(f"\n{'=' * 68}\n{name_a} vs {name_b}  ({len(papers)} paired papers)\n{'=' * 68}")

    # --- progress score (paired, per paper) ---
    ps_a = np.array([sum(arm_a[p]) / len(arm_a[p]) for p in papers])
    ps_b = np.array([sum(arm_b[p]) / len(arm_b[p]) for p in papers])
    diff = ps_a - ps_b
    obs = diff.mean()

    idx = RNG.integers(0, len(diff), size=(N_BOOT, len(diff)))
    boot = diff[idx].mean(axis=1)
    lo, hi = np.percentile(boot, [2.5, 97.5])

    signs = RNG.choice([-1.0, 1.0], size=(N_PERM, len(diff)))
    perm = (signs * diff).mean(axis=1)
    p_perm = (np.sum(np.abs(perm) >= abs(obs)) + 1) / (N_PERM + 1)

    print(f"progress score : {ps_a.mean()*100:.2f}% vs {ps_b.mean()*100:.2f}%  "
          f"= {obs*100:+.2f}pp")
    print(f"                 95% CI (bootstrap {N_BOOT}) [{lo*100:+.2f}, {hi*100:+.2f}] pp")
    print(f"                 permutation p = {p_perm:.4f}")

    wins_a = int(np.sum(diff > 0))
    wins_b = int(np.sum(diff < 0))
    print(f"per-paper wins : {name_a} {wins_a}, {name_b} {wins_b}, tied {len(papers)-wins_a-wins_b}")

    # --- paper passrate (final subtask only, per eval.py is_paper_correct) ---
    pa = [arm_a[p][-1] for p in papers]
    pb = [arm_b[p][-1] for p in papers]
    b = sum(1 for x, y in zip(pa, pb) if x and not y)
    c = sum(1 for x, y in zip(pa, pb) if y and not x)
    print(f"paper passrate : {sum(pa)}/{len(pa)} vs {sum(pb)}/{len(pb)}  "
          f"McNemar ({b} vs {c} discordant) p = {mcnemar_exact(b, c):.4f}")

    # --- subtask correctness (aligned by index; truncate to shorter run) ---
    sb = sc = total = 0
    for p in papers:
        for x, y in zip(arm_a[p], arm_b[p]):
            total += 1
            if x and not y:
                sb += 1
            elif y and not x:
                sc += 1
    print(f"subtask correct: {total} aligned subtasks, {sb} {name_a}-only vs "
          f"{sc} {name_b}-only  McNemar p = {mcnemar_exact(sb, sc):.4f}")


def main(base):
    arms = {}
    for name in ("memclaw", "mem0", "none"):
        path = os.path.join(base, name)
        if os.path.isdir(path):
            arms[name] = load_arm(path)
            n_sub = sum(len(v) for v in arms[name].values())
            print(f"loaded {name}: {len(arms[name])} papers, {n_sub} subtasks")

    for a, b in (("memclaw", "none"), ("mem0", "none"), ("memclaw", "mem0")):
        if a in arms and b in arms:
            compare(a, arms[a], b, arms[b])


if __name__ == "__main__":
    main(sys.argv[1])

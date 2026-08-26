"""Pooled math+phys significance for one agent-model tier.

Answers "what is the single combined score?" without the trap of averaging
two domains that differ in difficulty and in sample size (40 papers vs 20).

Three views, in increasing order of how much they assume:

  1. SUBTASKS SOLVED (the headline). Every subtask in both domains is one
     binary observation on a comparable unit, so they pool directly. Reported
     as "X of N" per arm plus an exact McNemar over the aligned pairs. This is
     the number to quote in a summary.

  2. PAPERS WON. Non-parametric and easy to read: across all 60 papers, how
     many did each arm score higher on.

  3. PROGRESS SCORE, DOMAIN-STRATIFIED. A naive pooled mean would let math's
     40 papers outvote physics's 20 while the two domains sit at different
     difficulty. So the per-domain mean difference is computed first and the
     two are averaged with equal weight, and the bootstrap resamples WITHIN
     each domain. The naive pooled figure is printed alongside it, clearly
     labelled, so the difference between the two is visible rather than
     hidden.

Usage:
    python scripts/pooled_stats.py <results/json/phys_TIER> <results/json/math_TIER>
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paired_stats import load_arm, mcnemar_exact  # noqa: E402

RNG = np.random.default_rng(20260826)
N_BOOT = 20000
N_PERM = 20000


def load_domain(root):
    """{arm: {paper: [is_correct, ...]}} for every arm subdir that has data."""
    arms = {}
    for entry in sorted(os.listdir(root)):
        path = os.path.join(root, entry)
        if not os.path.isdir(path) or entry.startswith("_"):
            continue
        data = load_arm(path)
        if data:
            arms[entry] = data
    return arms


def compare_pooled(name_a, name_b, domains):
    """domains: [(label, arms_dict), ...]"""
    present = [(lbl, d) for lbl, d in domains if name_a in d and name_b in d]
    if not present:
        return
    print(f"\n{'=' * 70}\n{name_a} vs {name_b}  (pooled over {len(present)} domains)\n{'=' * 70}")

    # --- 1. subtasks solved -------------------------------------------------
    tot_a = tot_b = tot_n = 0
    only_a = only_b = 0
    per_domain_diffs = []
    wins_a = wins_b = ties = 0

    for lbl, arms in present:
        A, B = arms[name_a], arms[name_b]
        papers = sorted(set(A) & set(B))
        d_a = d_b = d_n = 0
        diffs = []
        for p in papers:
            a, b = A[p], B[p]
            n = min(len(a), len(b))
            for i in range(n):
                if a[i] and not b[i]:
                    only_a += 1
                elif b[i] and not a[i]:
                    only_b += 1
            d_a += sum(a[:n]); d_b += sum(b[:n]); d_n += n
            psa, psb = sum(a) / len(a), sum(b) / len(b)
            diffs.append(psa - psb)
            if psa > psb:
                wins_a += 1
            elif psb > psa:
                wins_b += 1
            else:
                ties += 1
        tot_a += d_a; tot_b += d_b; tot_n += d_n
        per_domain_diffs.append(np.array(diffs))
        print(f"  {lbl:>6}: {len(papers)} papers, {d_n} subtasks | "
              f"{name_a} {d_a}/{d_n} ({100*d_a/d_n:.1f}%)  "
              f"{name_b} {d_b}/{d_n} ({100*d_b/d_n:.1f}%)")

    p_sub = mcnemar_exact(only_a, only_b)
    print(f"\n  SUBTASKS SOLVED (headline): {name_a} {tot_a}/{tot_n} "
          f"({100*tot_a/tot_n:.1f}%)  vs  {name_b} {tot_b}/{tot_n} "
          f"({100*tot_b/tot_n:.1f}%)")
    print(f"     net +{tot_a - tot_b} subtasks, "
          f"+{100*(tot_a-tot_b)/tot_n:.2f}pp")
    print(f"     McNemar exact on {only_a} vs {only_b} discordant: p = {p_sub:.4g}")

    # --- 2. papers won ------------------------------------------------------
    print(f"\n  PAPERS WON: {name_a} {wins_a}, {name_b} {wins_b}, tied {ties} "
          f"(of {wins_a + wins_b + ties})")

    # --- 3. progress score, domain-stratified -------------------------------
    naive = np.concatenate(per_domain_diffs)
    strat_obs = float(np.mean([d.mean() for d in per_domain_diffs]))

    boot = np.empty(N_BOOT)
    for k in range(N_BOOT):
        boot[k] = np.mean([
            d[RNG.integers(0, len(d), len(d))].mean() for d in per_domain_diffs
        ])
    lo, hi = np.percentile(boot, [2.5, 97.5])

    perm = np.empty(N_PERM)
    for k in range(N_PERM):
        perm[k] = np.mean([
            (d * RNG.choice([-1.0, 1.0], len(d))).mean() for d in per_domain_diffs
        ])
    p_perm = float((np.abs(perm) >= abs(strat_obs)).mean())

    print(f"\n  PROGRESS SCORE (domain-stratified, equal weight per domain):")
    print(f"     {100*strat_obs:+.2f}pp   95% CI [{100*lo:+.2f}, {100*hi:+.2f}]   "
          f"perm p = {p_perm:.4g}")
    print(f"     naive pooled mean over all {len(naive)} papers "
          f"(math outvotes phys, shown for contrast): {100*naive.mean():+.2f}pp")


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    domains = []
    for root in sys.argv[1:]:
        label = os.path.basename(root.rstrip("/\\")).split("_")[0]
        domains.append((label, load_domain(root)))
        print(f"loaded {label}: arms {sorted(domains[-1][1])}")

    arms_everywhere = set.intersection(*[set(d) for _, d in domains])
    order = [a for a in ("memclaw", "mem0", "none") if a in arms_everywhere]
    for i in range(len(order)):
        for j in range(i + 1, len(order)):
            compare_pooled(order[i], order[j], domains)


if __name__ == "__main__":
    main()

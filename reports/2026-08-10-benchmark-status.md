# Benchmark update — MemoryArena formal reasoning complete (MemClaw vs mem0 vs no-memory)

**Date:** 2026-08-10
**Scope:** MemoryArena-Rotation — travel, math, physics
**Agent model:** `openai/gpt-4.1` via OpenRouter for all headline numbers (judge held at
`openai/gpt-4o-mini` in every arm so the only variable is the memory system)
**Supersedes:** `2026-08-03-memoryarena-update.md` (gpt-4o-mini tier; kept as the
lower-model-tier comparison point)

---

## TL;DR

MemoryArena's formal-reasoning track is **finished** — both domains, all three arms.

- **MemClaw beats the no-memory control on both formal-reasoning domains, at
  significance.** Math +4.92pp progress score (p=0.024); physics +20.46pp
  (p=0.0036). Physics is the stronger and cleaner of the two despite half the
  sample.
- **mem0 is statistically indistinguishable from having no memory at all**, in
  both domains (math p=0.94, physics p=0.45). It stores something — just far
  less than MemClaw (319 vs 1422 tok/paper on math; 119 vs 1104 on physics) —
  and it does not show up in outcomes.
- **MemClaw beats mem0 by roughly the same margin it beats no-memory**, which is
  the more interesting framing: the win isn't "memory helps," it's "this memory
  system helps and a well-known alternative didn't."
- **Travel remains a true null** and is closed. That result stands and should be
  reported alongside the wins, not omitted.
- **The 2026-08-03 caution has been resolved in MemClaw's favour, not walked
  back.** What was an underpowered directional signal at gpt-4o-mini cleared
  significance once the agent model had headroom — which is exactly what we
  predicted would happen, and it replicated on a second domain.

---

## Please read this before quoting a number

These are real, paired, controlled results and they can be shared. Two limits
matter:

1. **This is formal-reasoning tasks at a gpt-4.1-tier agent.** Travel was a
   genuine null at gpt-4o-mini and has never been retested at gpt-4.1. We have
   no evidence yet that this generalizes to other task shapes.
2. **Within each domain, the three metrics are correlated, not three
   independent confirmations.** Paper passrate is literally the final-subtask
   slice of subtask correctness, and progress score is another aggregation of
   the same per-subtask outcomes. Two *domains* agreeing is the real
   replication; three metrics agreeing within a domain is one result seen three
   ways.

The defensible statement today is:

> On both of MemoryArena's formal-reasoning domains, with a gpt-4.1 agent,
> MemClaw significantly outperformed both a no-memory control and mem0, while
> mem0 was indistinguishable from no memory. The effect did not appear on the
> travel domain at a weaker agent model.

---

## What was run

| domain | scale | arms | status |
|---|---|---|---|
| math (formal reasoning) | 40 papers / 354 subtasks — **full test split** | memclaw, mem0, none | ✅ complete |
| physics (formal reasoning) | 20 papers / 86 subtasks — **full split** | memclaw, mem0, none | ✅ complete |
| travel | 50 groups / 340 persons | memclaw, none | ✅ closed — null result |
| shopping | — | — | deferred, heavy setup |

Every arm within a domain ran the **same items** with configs verified identical
apart from the memory system, so all comparisons are paired.

Method (unchanged from prior reports): paired bootstrap CI (20k) plus sign-flip
permutation test over per-paper scores, and exact McNemar tests for the two
binary metrics. A raw aggregate delta is not treated as evidence.

---

## Results

### Math — 40 papers / 354 subtasks

| arm | paper passrate | avg progress score | avg memory length |
|---|---|---|---|
| memclaw | **0.250** (10/40) | **23.95%** | 1422 tok |
| mem0 | 0.100 (4/40) | 19.15% | 319 tok |
| none | 0.100 (4/40) | 19.03% | 0 tok |

| comparison | metric | result | p |
|---|---|---|---|
| memclaw vs none | progress score | +4.92pp, 95% CI [+0.87, +9.04] | **0.024** |
| memclaw vs none | subtask correctness | 29 vs 14 own-only | **0.031** |
| memclaw vs none | paper passrate | 6 vs 0 discordant | **0.031** |
| mem0 vs none | progress score | +0.12pp, 95% CI [−2.93, +3.22] | 0.94 |
| mem0 vs none | paper passrate | 4/40 vs 4/40 — identical | 1.00 |
| mem0 vs none | subtask correctness | 13 vs 11 own-only | 0.84 |
| memclaw vs mem0 | progress score | +4.81pp, 95% CI [+1.13, +8.42] | **0.014** |
| memclaw vs mem0 | paper passrate | 6 vs 0 discordant | **0.031** |
| memclaw vs mem0 | subtask correctness | 26 vs 13 own-only | 0.053 (n.s.) |

Per-paper wins: memclaw 15, none 6, tied 19. mem0 vs none was 8–8 with 24 ties —
a coin flip.

Effect roughly **doubled** versus the gpt-4o-mini run (+2.37pp → +4.92pp),
consistent with the "weaker model leaves no headroom" diagnosis from the
2026-08-03 report.

### Physics — 20 papers / 86 subtasks

| arm | paper passrate | avg progress score | avg memory length |
|---|---|---|---|
| memclaw | **0.350** (7/20) | **52.75%** | 1104 tok |
| mem0 | 0.100 (2/20) | 36.26% | 119 tok |
| none | 0.050 (1/20) | 32.29% | 0 tok |

| comparison | metric | result | p |
|---|---|---|---|
| memclaw vs none | progress score | +20.46pp, 95% CI [+8.58, +34.17] | **0.0036** |
| memclaw vs none | subtask correctness | 21 vs 3 own-only | **0.0003** |
| memclaw vs none | paper passrate | 6 vs 0 discordant | **0.031** |
| mem0 vs none | progress score | +3.97pp, 95% CI [−5.56, +14.14] | 0.45 |
| mem0 vs none | paper passrate | 2/20 vs 1/20 | 1.00 |
| mem0 vs none | subtask correctness | 7 vs 3 own-only | 0.34 |
| memclaw vs mem0 | progress score | +16.49pp, 95% CI [+6.42, +27.00] | **0.0067** |
| memclaw vs mem0 | subtask correctness | 20 vs 6 own-only | **0.0094** |
| memclaw vs mem0 | paper passrate | 5 vs 0 discordant | 0.0625 (n.s.) |

Per-paper wins vs none: memclaw **9, none 0**, tied 11 — the control did not win
a single paper.

**On the two "not significant" cells above:** memclaw-vs-mem0 paper passrate at
p=0.0625 is the *best mathematically achievable* p-value for 5-vs-0 discordant
pairs under an exact binomial test. At this sample size that metric cannot go
lower no matter how lopsided the outcome. It is a resolution limit, not evidence
against the effect — the subtask (p=0.0094) and progress-score (p=0.0067)
numbers carry the real signal. Please don't quote the 0.0625 as a negative.

### Travel — closed, no effect

Settled at gpt-4o-mini: +1.06pp SPS, 95% CI [−1.63, +3.76], permutation
p=0.448, group wins 24/21/5 ties. The gap *shrank* as n grew, which is noise
regressing rather than signal emerging. Detecting an effect that size would need
~678 groups; the benchmark has 270. **Not worth re-running for group count** —
if travel is revisited, the change should be the agent model, matching what
worked on math and physics.

---

## Why the mem0 finding needs a caveat attached

mem0's ingestion is **asynchronous** — fact extraction runs server-side and
memories were not searchable ~30s after an `add` in manual testing. If our
subtask-to-subtask timing is faster than mem0's ingestion latency, its arm could
look artificially weak for reasons unrelated to memory quality.

We deliberately did not engineer around this: it is realistic mem0 behaviour that
any user would hit. But when this number goes external, it should be stated as
*"mem0 as configured out of the box, at this task's pacing"* — not as a claim
about mem0's retrieval quality in general.

---

## Reproducibility

The paired-statistics script is now checked into this repo at
`scripts/paired_stats.py` (it had been rewritten from scratch three times from
scratchpad copies). It computes all three pairwise comparisons directly from the
raw per-paper `result.jsonl` logs:

```
python scripts/paired_stats.py <MemoryArena>/results/json/phys_gpt41
```

Re-running it reproduced the 2026-08-04 memclaw-vs-none physics figures to
within bootstrap-seed noise (perm p 0.0038 vs 0.0036 recorded), which
independently validates both the earlier result and the script.

One process note worth flagging: the physics mem0 arm actually **ran on
2026-08-05 and then sat unscored on disk until 2026-08-09** — a completed result
nobody could see. Scoring now happens in the same pass as the run.

---

## Next steps, in priority order

**1. LoCoMo / LongMemEval — the only priority-1 item.** These are the
recall-accuracy benchmarks this repo was built for. Everything above is external
MemoryArena work.

The product repo (`caura-ai/caura-memclaw` → `BENCHMARKS.md`, last run
**2026-04-19**) already publishes LoCoMo **77.6%** and LongMemEval **72.5%**
LLM-judge accuracy, plus **96.6% / 98.2%** token savings vs full context. **This
does not close the item.** Per that document itself, those figures come with no
baseline or competitor arm, no stated sample size, no named judge or answering
model, and no statistical test — it asserts "MemClaw, Mem0, Zep land in a narrow
band" without giving the figures. That's the uncontrolled-aggregate shape our own
method note rejects, and it's the reason the MemoryArena results above are
defensible while a bare accuracy number isn't.

**So the job isn't to reproduce 77.6% — it's to produce the comparative,
paired version**: memclaw / mem0 / full_context / no_memory on the same
questions, with bootstrap CIs and McNemar. Treat 77.6/72.5 as a sanity-check
target for our memclaw arm — landing far off it means our harness or seeding is
wrong, not that the product regressed.

Scoped 2026-08-09; it is more than a dataset download:

- Dataset fetch + convert — the fetch script referenced in the dataset README
  was never written; both datasets need converting to the harness's flat
  conversation/qa JSONL pair.
- **The baseline arms don't produce scoreable output.** Only the memclaw
  condition writes per-question records; `full_context` and `no_memory` print an
  aggregate and keep nothing. The paired method used for every result above
  **cannot be applied until this is fixed** — without it we'd get a raw
  aggregate delta, which is exactly what our own method note rejects as
  evidence. Fix before running anything.
- **No mem0 arm exists in this harness.** MemoryArena's headline is now
  three-way; this needs to match to be comparable.
- One conversation per invocation — needs a loop plus a combine step.

Also note the judge here is `claude-sonnet-5` via the Anthropic API — a
different provider and key from the OpenRouter setup all MemoryArena work used.

**One tension to settle while we're in there.** `BENCHMARKS.md` claims **96.6% /
98.2% token savings vs full context**. Our travel measurement pointed the other
way: MemClaw used **112k input tokens/group vs 104k** for the control — about 7%
*more* — and that control inlines all prior plans, so it is a full-context-style
comparator. Both can be true; the tasks and pipelines differ. But the two numbers
shouldn't circulate side by side unreconciled, and the `full_context` arm of the
recall harness is exactly what settles it. Fixing the per-question-records gap
above also unblocks this measurement.

**2. MemoryArena shopping** — more worth doing now that two formal-reasoning
domains discriminate, since it's a differently-shaped task. Still a heavy,
deliberate setup: multi-GB product DB, a JDK, a spacy model, and a separate
upstream service.

**3. Housekeeping** — investigate an abandoned 2-paper partial run found in the
results tree (origin unknown); pull over the CL-Bench quick_test results from
whichever machine actually ran them, so they can be cited with real numbers
instead of "ran elsewhere."

**4. Optional, for an external writeup only** — a pooled math+physics estimate.
This needs a domain fixed-effect, not a naive average; the two domains have
different task structure and difficulty.

**Still blocked:** STATE-Bench, pending an Azure OpenAI resource with a GPT-5.4
deployment (its eval protocol locks the judge and user-simulator to Azure only;
our OpenRouter key can't cover it).

# memclaw-benchmarks

Benchmark suite for [MemClaw](https://memclaw.net): does memclaw's recall
actually beat having no memory at all, and does it hold up against public
long-term-memory QA benchmarks the rest of the field uses?

Every comparison in this repo is **paired and controlled** — memclaw and
each baseline (no-memory, and where possible mem0) run the *same* items, and
a gap is only reported as a finding once it clears a bootstrap CI and a
permutation or McNemar test. We also publish the negative results, not just
the wins — see Travel below. If a number here isn't backed by a control arm
and a significance test, treat it as a lead, not a result.

## What's here

| Suite | Dataset | Status |
|---|---|---|
| `suites/recall_accuracy_locomo` | LOCOMO | Scaffolded, not populated — **priority 1** |
| `suites/recall_accuracy_longmemeval` | LongMemEval | Scaffolded, not populated — **priority 1** |

Each suite runs three conditions per question — memclaw recall / full-context
dump / no-memory blind — and scores answers with an LLM judge
(paraphrase-tolerant correctness, same methodology mem0's own benchmarks use).

MemClaw's product repo already publishes uncontrolled LoCoMo/LongMemEval
numbers (77.6% / 72.5% LLM-judge accuracy, `caura-ai/caura-memclaw` →
`BENCHMARKS.md`, run 2026-04-19) — but with no baseline arm, no stated sample
size, no named judge, and no significance test. The job here isn't to
reproduce those two numbers; it's to produce the paired, baselined version
that number can't stand in for. Treat 77.6% / 72.5% as a sanity-check target
for our own memclaw arm, not as a finished benchmark.

## MemoryArena-Rotation (external benchmark)

Before investing further in the LOCOMO/LongMemEval datasets above, we ran
memclaw against [MemoryArena](https://huggingface.co/datasets/ZexueHe/memoryarena)
(sibling repo, not part of this codebase) as an early, cheaper read on whether
memory helps at all — and, once it clearly did, added mem0 as a third arm.
See `CLAUDE.md` for full methodology, raw numbers, and caveats — this is the
summary.

| Domain | Agent model | memclaw vs none | memclaw vs mem0 | mem0 vs none |
|---|---|---|---|---|
| Travel (50 groups) | gpt-4o-mini | **No effect** (95% CI spans zero, p=0.45) | — | — |
| Math (40 papers / 354 subtasks) | gpt-4.1 | **memclaw wins** — progress score +4.9pp (p=0.024), pass rate 10/40 vs 4/40 (p=0.031) | +4.8pp (p=0.014) | +0.1pp, n.s. (p=0.94) |
| Physics (20 papers / 86 subtasks) | gpt-4.1 | **memclaw wins, larger effect** — progress score +20.5pp (p=0.0036), pass rate 7/20 vs 1/20 (p=0.031), memclaw won every paper it didn't tie (9-0-11) | +16.5pp (p=0.0067) | +4.0pp, n.s. (p=0.45) |
| Physics (20 papers / 86 subtasks) | gemini-3.6-flash | **memclaw wins, replicates & strengthens gpt-4.1** — progress score +24.1pp (p=0.0013), subtask McNemar p=4.2e-07 | not run (mem0 quota) | not run (mem0 quota) |
| Math (40 papers / 354 subtasks) | gemini-3.6-flash | ⛔ not scoreable — result set was silently corrupted by an unhandled billing failure and repair is blocked on account funding | — | mem0 arm complete and clean, not yet paired against a valid none/memclaw pair |
| Shopping | — | deferred — needs a multi-GB product DB + separate service, not yet started | — | — |

**Takeaway:** memory only showed an effect once the agent model had headroom
to use it — gpt-4o-mini couldn't do the travel task well enough for memory to
matter regardless of condition. At gpt-4.1, memclaw beat both no-memory and
mem0 on both formal-reasoning domains, and **mem0 was statistically
indistinguishable from no memory at all** in both. The effect held and grew
when we swapped in a second agent model family (`gemini-3.6-flash`) on
physics, so this isn't a gpt-4.1 artifact. Not yet tested: whether this holds
outside formal-reasoning-style tasks, or at gpt-4.1 on the travel domain
specifically.

**Known limitation — read before quoting absolute scores.** Every
formal-reasoning result above was produced by a single-shot reasoner, not the
tool-using agent loop the harness intends: a config bug points the tool-loop
client at the wrong API base, it 401s, and the harness silently falls back to
a plain reasoning call. This hit **every arm identically** (708/708 stored
subtasks carry the same auth error), so the paired memclaw-vs-mem0-vs-none
comparisons above are unaffected — but the absolute progress-score and
pass-rate numbers are a floor on what the agent could do, not its real
capability. Left unfixed on purpose so new model tiers stay comparable to the
existing baseline; fixing it means re-running gpt-4.1 too.

## Setup

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=...
export MEMCLAW_API_KEY=...
export MEMCLAW_BASE_URL=https://memclaw.net   # or your deployment
```

`runners/memclaw_client.py` maps memclaw operations to REST endpoints. The
exact paths are a best-effort guess based on the MCP tool set — verify them
against your memclaw deployment's REST docs (`MEMCLAW_*_PATH` env vars let
you override any of them without touching code) before trusting results.

Datasets need populating first — see `datasets/locomo/README.md` and
`datasets/longmemeval/README.md`.

## Running

```bash
# sanity-check on a handful of questions first
python suites/recall_accuracy_locomo/run.py --condition memclaw --limit 5
python suites/recall_accuracy_locomo/run.py --condition full_context --limit 5
python suites/recall_accuracy_locomo/run.py --condition no_memory --limit 5
```

Each run writes a JSON file to `results/` with per-item detail plus an
aggregate metric, so results are diffable across runs over time.

## Methodology

A raw aggregate delta is not treated as evidence anywhere in this repo. Every
reported comparison:

- runs memclaw and its baseline(s) on the **same items** (paired, not two
  independent samples);
- reports a **95% bootstrap CI** (20k resamples) and a **permutation test**
  for continuous metrics, or an **exact McNemar test** for pass/fail metrics;
- gets checked for **silently-corrupted data** before it's cited — a run
  logging "N attempted, 0 failed" only means every item wrote *a* result, not
  a *correct* one (see the gemini-3.6-flash math entry above for why this
  matters in practice).

`scripts/paired_stats.py` implements the bootstrap/permutation/McNemar suite
and runs against any MemoryArena results directory:

```bash
python scripts/paired_stats.py <MemoryArena>/results/json/phys_gpt41
```

Dated write-ups with full numbers, caveats, and per-domain breakdowns live in
`reports/`.

## Other benchmark tracks

MemClaw is also being evaluated in three sibling repos outside this
codebase's scope — tracked in `CLAUDE.md` since state has to survive across
sessions and machines:

| Benchmark | Status |
|---|---|
| CL-Bench (`continual-learning-bench`) | MemClaw integrated as a system; a run reportedly happened but its results aren't recovered into this record yet |
| STATE-Bench | Blocked — its eval protocol locks the judge/simulator to Azure OpenAI GPT-5.4, which we don't have provisioned |
| GroupMemBench | Queued, not yet scoped |

## Repo layout

```
datasets/       public dataset caches (locomo, longmemeval)
suites/         one dir per benchmark, each with a run.py entrypoint
runners/        shared harness + memclaw REST client
judges/         LLM-judge scoring
scripts/        paired-comparison statistics (bootstrap CI, permutation, McNemar)
reports/        dated result write-ups with full numbers and caveats
results/        one JSON file per run
```

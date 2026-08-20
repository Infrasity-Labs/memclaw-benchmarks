# caura-benchmarks

*(formerly `memclaw-benchmarks` — [Caura](https://caura.ai) is the rebrand of
MemClaw, same product/team/API. The `memclaw_*` tool names, env vars, and
URLs still work by design, so nothing in this harness needed a functional
change — only names in prose and links to the product repo were updated.)*

Benchmark suite for [Caura](https://caura.ai): does its recall actually beat
having no memory at all, and does it hold up against public long-term-memory
QA benchmarks the rest of the field uses?

Every comparison in this repo is **paired and controlled** — caura (memclaw)
and each baseline (no-memory, and where possible mem0) run the *same* items,
and a gap is only reported as a finding once it clears a bootstrap CI and a
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

Caura's product repo already publishes uncontrolled LoCoMo/LongMemEval
numbers (77.6% / 72.5% LLM-judge accuracy, `caura-ai/caura` →
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
| Physics (20 papers / 86 subtasks) | gemini-3.6-flash | **memclaw wins, replicates & strengthens gpt-4.1** — progress score +24.1pp (p=0.0013), subtask McNemar p=4.2e-07 | not run (mem0 quota, since resolved) | not run |
| Math (40 papers / 354 subtasks) | gemini-3.6-flash | **memclaw wins, replicates gpt-4.1** — progress score +7.8pp (p=0.0006), subtask McNemar p=0.0007 (paper-passrate McNemar n.s. at 0.125 — known floor effect, not evidence against) | subtask McNemar p=0.040 (progress-score gap n.s.) | +3.7pp, trending but n.s. (p=0.076) — **not** a repeat of gpt-4.1's clean null, see caveat below |
| Shopping | — | deferred — needs a multi-GB product DB + separate service, not yet started | — | — |

**Takeaway:** memory only showed an effect once the agent model had headroom
to use it — gpt-4o-mini couldn't do the travel task well enough for memory to
matter regardless of condition. At gpt-4.1, memclaw beat both no-memory and
mem0 on both formal-reasoning domains, and **mem0 was statistically
indistinguishable from no memory at all** in both. The effect held and grew
at a second agent model family (`gemini-3.6-flash`), on **both** domains now
— math replicated as of 2026-08-19, after the corruption/funding blocker
below was cleared. **mem0's picture at the gemini tier is less clean than at
gpt-4.1**: on math it trends above no-memory (p=0.076, not significant) where
gpt-4.1 was a flat null (p=0.94) — one data point, not yet a second
replication either way; the still-unrun physics mem0/gemini arm is what
would settle it. Not yet tested: whether any of this holds outside
formal-reasoning-style tasks, or at gpt-4.1 on the travel domain specifically.

**Known limitation — read before quoting absolute scores.** Every
formal-reasoning result above was produced by a single-shot reasoner, not the
tool-using agent loop the harness intends: a config bug points the tool-loop
client at the wrong API base, it 401s, and the harness silently falls back to
a plain reasoning call. This hit **every arm identically**, so the paired
memclaw-vs-mem0-vs-none comparisons above are unaffected — but the absolute
progress-score and pass-rate numbers are a floor on what the agent could do,
not its real capability. Left unfixed on purpose so new model tiers stay
comparable to the existing baseline; fixing it means re-running gpt-4.1 too.

**Data-integrity note.** The gemini-3.6-flash math result above was blocked
for a week by a silent failure mode: an exhausted account balance was
swallowed as an empty "completed" response instead of a failure, so a run
could log "0 failed" while actually being contaminated. Caught by a
dedicated contamination scanner, not by the run's own exit code — see
Methodology below. Every result in this table has since been passed through
that scanner before being cited.

## Setup

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=...
export MEMCLAW_API_KEY=...
export MEMCLAW_BASE_URL=https://caura.ai   # or your deployment
```

`runners/memclaw_client.py` maps memclaw operations to REST endpoints. The
exact paths are a best-effort guess based on the MCP tool set — verify them
against your Caura deployment's REST docs (`MEMCLAW_*_PATH` env vars let you
override any of them without touching code) before trusting results. Caura
keeps the `memclaw_*`/`MEMCLAW_*` names for backward compatibility, so none
of this needs renaming to work against a current deployment.

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
  a *correct* one (see the data-integrity note above for why this matters in
  practice, not just in theory).

`scripts/paired_stats.py` implements the bootstrap/permutation/McNemar suite
and runs against any MemoryArena results directory:

```bash
python scripts/paired_stats.py <MemoryArena>/results/json/phys_gpt41
```

Dated write-ups with full numbers, caveats, and per-domain breakdowns live in
`reports/`.

## Other benchmark tracks

Caura is also being evaluated in three sibling repos outside this codebase's
scope — tracked in `CLAUDE.md` since state has to survive across sessions and
machines:

| Benchmark | Status |
|---|---|
| CL-Bench (`continual-learning-bench`) | Integrated as a system; a run reportedly happened but its results aren't recovered into this record yet |
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

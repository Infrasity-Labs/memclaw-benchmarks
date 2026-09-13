# memclaw-benchmarks — working notes

Benchmark suite for MemClaw. See `README.md` for the full track A/B design
(recall accuracy vs. MemClaw-specific governance/fleet-memory differentiators).
This file tracks *which benchmarks are done, in progress, or queued* across
both this repo and the sibling `continual-learning-bench` repo, so state
survives across sessions.

**Rebrand note (2026-08-20):** MemClaw is now **Caura** — product repo moved
to `caura-ai/caura`, site is `https://caura.ai`. Per Caura's own repo, the
`memclaw_*` tool names, env vars (`MEMCLAW_API_KEY`, etc.), and URLs keep
working for backward compatibility, so nothing in this repo's harness code
needed a functional change. Below, "MemClaw"/"memclaw" is left as-is in
already-written historical entries (that was the correct name when written,
and it matches the still-functional identifiers in code/config); new entries
should say Caura. Only the direct product-repo pointer (the old
`caura-ai/caura-memclaw` name → now `caura-ai/caura`) has been corrected
throughout, since that one was just wrong going forward, not a historical fact.

## Benchmark status

| Benchmark | Status | Where | Notes |
|---|---|---|---|
| CL-Bench | ✅ **quick_test ran on the other machine 2026-08-19** (smoke only, not a result); ⛔ **default schedule still blocked as of 2026-08-26** — now on OpenRouter `in_flight_budget_exhausted`, a different mechanism from the earlier spend-rate cap. ~~**Still zero memclaw scores in THIS checkout**~~ — **false, corrected 2026-09-08: three completed memclaw trace groups are here, all `quick_test` at gpt-4o (noise-scale, still not a result). Zero memclaw runs on the `default` schedule remains true.** | `continual-learning-bench` — this checkout is on `add-memclaw-system` (`6dffa27`), clean, pushed to `myfork` (`jy7lsna/continual-learning-bench`). The machine with results has it at `~/continual-learning-bench/continual-learning-bench` | See "CL-Bench: state as of 2026-08-26" below and **"CL-Bench: what is actually on disk here (2026-09-08)"**, which corrects this cell. ~~Everything in this clone's `results/` is ... `system: icl` (gpt-5 baseline), three runs named `failed_quick_test_*`~~ — **wrong on both counts.** All five trace groups are dated 2026-07-28 and all ran `openrouter/openai/gpt-4o`; **three of the five are `system: memclaw`**, all `status: completed` with real per-instance rewards, and one is a **completed `icl` run on the full `default` schedule (5 runs × 120 instances)**. `final_results/runs/` is upstream's shipped leaderboard data (gpt-5.4), not ours. ~~Blockers here: (a) no memclaw config; (b) `.env` has only `MEMCLAW_API_KEY`~~ — **both stale, re-verified 2026-09-08: `configs/poker/memclaw.json` exists (committed `cf29fc2`, 2026-09-02, default schedule at `openrouter/openai/gpt-5.4` to match the shipped `mem0-gpt-5.4`/`icl-gpt-5.4` baselines) and `.env` carries `OPENROUTER_API_KEY` alongside `MEMCLAW_API_KEY`.** The `in_flight_budget_exhausted` fix is also already implemented in the same commit (`CLBENCH_MAX_OUTPUT_TOKENS`, see below). **CL-Bench is now blocked on LLM spend only.** |
| STATE-Bench | ✅ **COMPLETE — Agent Learning Track run 2026-08-26 on the other machine**: 3 domains × 2 arms × 5 runs × 50 test tasks = **1500 trajectories, 0 errors**. memclaw wins clearly on 2 of 3 domains, roughly flat on the third | `STATE-Bench` — on the run machine at `Downloads/STATE-Bench` (**not** `~/STATE-Bench` as earlier notes said). This checkout is a separate, unrun copy | See "STATE-Bench: Agent Learning Track — first full run" below for the results table and the six real bugs fixed along the way. Both prior blockers resolved 2026-08-26: a working `MEMCLAW_API_KEY` and a real Azure AI Foundry **gpt-5.4 deployment**. Note `STATE_BENCH_EVAL_ENDPOINT` must be the bare resource root (`https://jyolsna.services.ai.azure.com`) — `client.py::_azure_openai_v1_base_url` appends `/openai/v1/` itself, so the AI Foundry *project* path 404s. |
| MemoryArena-Rotation (travel) | ✅ **settled — negative result, do not re-run** | `MemoryArena` repo (sibling dir), cloned | See "MemoryArena travel: settled" section below. memclaw vs no-memory are statistically indistinguishable at n=50 groups, and the benchmark is too small to ever resolve the observed effect. Travel is closed unless the agent model changes. |
| MemoryArena-Rotation (math) | ✅ **significant win at gpt-4.1** (memclaw vs none); mem0 arm ✅ **run 2026-08-04 on a second machine — mem0 ≈ none, memclaw beats both**; ✅ **gemini-3.6-flash tier complete 2026-08-19** (memclaw vs none significant, +7.76pp progress score, subtask McNemar p=0.0007 — replicates phys at this tier; mem0 comparison softer than gpt-4.1's, not a clean "mem0≈none" repeat — see "MemoryArena math: gemini-3.6-flash — complete" below) ; ✅ **gpt-5.6-sol tier complete 2026-08-26 on Azure, RE-JUDGED 2026-08-27 on the common `gpt-4o-mini` ruler: +7.02pp progress score, perm p=0.0054, subtask McNemar p=0.0011 — significant. (The originally-reported +4.16pp p=0.141 was a `gpt-5-mini` judge artifact; superseded.) See "gpt-5.6-sol RE-JUDGED on the common ruler" below.** mem0 arm at this tier stopped at **15/40 papers** — clean, resumable, do not quote beside the 40-paper numbers | `MemoryArena` repo, `run_math.py` + `configs/formal_reasoning_configs/math_memclaw_gpt41.json` / `math_none_gpt41.json` / `math_mem0_gpt41.json` (+ `*_gemini36.json` variants) | Self-contained (HF dataset `ZexueHe/memoryarena`, config `formal_reasoning_math`): **40 papers / 354 subtasks**. gpt-4o-mini run (2026-08-02) was directional but underpowered; gpt-4.1 rerun (2026-08-04) cleared significance on all three metrics — see "MemoryArena math: gpt-4.1 rerun" below. mem0 arm completed same day on a second (higher-RAM) machine after the primary machine OOM'd — see "MemoryArena math: mem0 arm result" below. ~18s/subtask → ~106 min sequential, ~27 min at 4 shards. See "MemoryArena math: setup gotchas" below — several traps cost real time. ~~Math has **no token/cost tracking at all**~~ — **corrected 2026-09-07**: `OpenAIBackend` *does* read `response.usage` and accumulates `usage_totals` (`llm_backend.py:124-127`), but nothing ever read those counters and `result.jsonl` carries no usage fields, so no historical per-run figure is recoverable and spend for past runs must come from OpenRouter's key API. `run_math.py` now writes `usage.json` beside each paper's results, so runs from 2026-09-07 onward do carry token counts. It also runs an **LLM judge** through OpenRouter (`env_config.model_name`), billing roughly double per subtask. Resumable per-paper via `_is_paper_processed`. Note: `results/json/math_gpt5mini/` holds an **abandoned partial run** (2 papers, memclaw only, no logs) from a `math_memclaw_gpt5mini.json`/`math_none_gpt5mini.json` config pair found already in the repo but never mentioned in this file before 2026-08-04 — origin unknown, not part of any tracked result, safe to ignore or resume separately. |
| MemoryArena-Rotation (phys) | ✅ **significant win at gpt-4.1 — stronger than math** (memclaw vs none); mem0 arm ✅ **run 2026-08-05 — mem0 ≈ none, memclaw beats both**; ✅ **replicated at `google/gemini-3.6-flash` 2026-08-12 with a larger effect** (+24.14pp, subtask McNemar p=4.2e-07); ✅ **gemini mem0 arm run 2026-08-20 — memclaw still wins (progress score p=0.035, subtask p=0.0005), mem0 vs none trends positive but not significant (p=0.17), matching the same soft trend seen in math-gemini** ; ✅ **mem0 arm run 2026-08-27 on OpenRouter — mem0 ≈ none (subtask McNemar p=1.0, an exact coin flip), memclaw beats mem0 (subtask p=0.015): the strong baseline does NOT lift mem0**; ✅ **claude-opus-5 tier COMPLETE 20/20 as of 2026-09-13 (was 17/20): +16.88pp progress score, paper passrate McNemar p=0.0039, subtask p=0.00019; a LARGE effect at a frontier model, which breaks the "effect erodes as agents get stronger" reading and points at the gpt-5.6-sol judge swap as the real cause — see "MemoryArena phys: claude-opus-5" below**; ✅ **gpt-5.6-sol tier run 2026-08-25 on Azure, RE-JUDGED 2026-08-27: on the common `gpt-4o-mini` ruler the gap is +12.37pp (subtask p=0.043), not +9.07pp — the no-memory baseline was 47.81%, not the 53.64% the swapped `gpt-5-mini` judge reported. The "baseline catches up / effect erodes" reading is WITHDRAWN. See "gpt-5.6-sol RE-JUDGED on the common ruler" below** | `MemoryArena` repo, `run_math.py` + `configs/formal_reasoning_configs/phys_memclaw_gpt41.json` / `phys_none_gpt41.json` / `phys_mem0_gpt41.json` (+ `*_gemini36.json` variants) | Second formal-reasoning domain, run as a replication of the math gpt-4.1 result. **20 papers / 86 subtasks**, same infra as math (shares `MathEnvironment`/env server/judge). See "MemoryArena phys: gpt-4.1 replication" below — effect is larger and cleaner than math despite half the sample (progress score +20.46pp vs +4.92pp, subtask McNemar p=0.0003 vs p=0.031). memclaw won every paper it didn't tie (9-0-11), none never won one. mem0 arm ran 2026-08-05 at `-Shards 1` on this machine and replicates math's mem0 finding — see "MemoryArena phys: mem0 arm result" below. **All three arms of both formal-reasoning domains are now complete at both gpt-4.1 and gemini-3.6-flash tiers.** |
| MemoryArena-Rotation (shopping) | ⛔ blocked on a large data download | `MemoryArena` repo, `run_shopping.py` + `configs/web_shopping_configs/memclaw.json` | Not runnable as-is: `data/shopping/` does not exist in this checkout and the config points at it (`upstream_webshop_data_root`). Needs the product DB from <https://huggingface.co/datasets/ai-hyz/MemoryArena-product-db> (`items_shuffle.json`, `items_ins_v2.json`, `domain_data.json`, a pyserini `search_engine/indexes-full/` index, `product_catalog/`), **plus** a JDK on `PATH` for the search engine and `pip install -r env/env_systems/web_shopping_env/requirements-shopping.txt` + `python -m spacy download en_core_web_lg`. It also boots a separate upstream WebShop service on port 36004. Do this setup deliberately — it is much heavier than travel/math. |
| GroupMemBench | ✅ **memclaw baseline built + verified 2026-08-19** on the other machine; ✅ **ingest throughput SOLVED 2026-09-02 — ~19h/domain → ~1.3h, measured, 720 writes 0 errors, $0**; ⛔ full run now gated only on LLM spend for the QA half | `~/GroupMemBench` **is present in this checkout** (corrected 2026-09-02 — the repo is here; only `baselines/memclaw/` is missing, that lives on the other machine). Also at `~/GroupMemBench` there (`UCSB-NLP-Chang/GroupMemBench`, commit `e2682e0`) | Group-conversation memory benchmark: 4 domains (Finance/Technology/Healthcare/Manufacturing) of synthetic multi-channel enterprise chat, 6 question types per domain, two pre-existing RAG baselines (BM25, `text-embedding-3-large`). A third was added: `baselines/memclaw/`. Confirmed 2026-09-02: **30,000 messages per domain, 120,000 writes total**. See "GroupMemBench: memclaw baseline" below — smoke-scale 3-way result, and "Ingest throughput: SOLVED" for the concurrency/session-reuse measurement that unblocked it. |
| LoCoMo | ❌ **dropped 2026-08-25** | `suites/recall_accuracy_locomo` (scaffolded, never populated) | Decision: not doing this. Scaffolding left in place, unpopulated. Product repo publishes 77.6% LLM-judge accuracy / 96.6% token savings (2026-04-19, `caura-ai/caura` → `BENCHMARKS.md`) with no baseline arm, no n, no judge model and no stats — that uncontrolled number is now the only LoCoMo figure this project will have. |
| LongMemEval | ❌ **dropped 2026-08-25** | `suites/recall_accuracy_longmemeval` (scaffolded, never populated) | Decision: not doing this. Same as LoCoMo — product repo's 72.5% accuracy / 98.2% token savings (2026-04-19) stands unbaselined. |

## MemoryArena travel: settled (2026-08-02) — negative result

Ran both arms at **50 groups / 340 persons** on `openai/gpt-4o-mini` via
OpenRouter, same 50 groups each (`results/travel/results.csv`):

| arm | groups | PS | SPS | SR |
|---|---|---|---|---|
| memclaw | 50 | 0.29% | 14.87% | 0.00% |
| none    | 50 | 0.29% | 13.81% | 0.00% |

**The +1.06pp SPS gap is not significant.** SPS is an unweighted mean over
per-group scores and both arms ran identical groups, so it's paired data
(50 obs). Paired analysis:

- 95% CI (bootstrap, 20k): **[−1.63, +3.76] pp** — spans zero
- permutation test (sign-flip, 20k): **p = 0.448**
- group-level wins: memclaw 24, none 21, tied 5 — a coin flip
- stdev of paired diffs: **9.86pp**, ~9x the effect

**Do not run the full 270 groups to try to resolve this.** Power analysis:
detecting a 1.06pp effect at that variance needs **~678 groups** for 80%
power; the benchmark only has 270. The smallest effect detectable at n=270
is 1.68pp — *larger* than what was observed. The full run cannot reach
significance for an effect this size, so the ~4-5 hrs is not worth spending.

The earlier "+1.7pp at n=13" reading was noise: the gap *shrank* toward zero
as n grew (1.72pp → 1.06pp), which is the signature of regression, not signal.

**No token-efficiency win either.** Hypothesis was that memory would beat
stuffing all prior plans into context. On 25 groups per arm, memclaw used
**112k input tokens/group vs none's 104k** — memclaw is ~1.07x *more*
expensive, not cheaper. Indicative only (the two 25-group subsets differ),
but it rules out a large efficiency advantage.

**Why travel can't discriminate at this model tier:** SR is 0/50 for both
arms and PS is 1/340 — literally the same single person passes in both. All
discriminating power sits in SPS, a partial-credit constraint score.
gpt-4o-mini simply cannot do this task, so there's no headroom for memory to
matter. If travel is revisited, change the **agent model** (gpt-4.1 / Sonnet
at ~20 groups to check for headroom), not the group count.

### Travel harness changes made (in `MemoryArena`, uncommitted)

- `run_travel.py`: added `TRAVEL_SHARD_COUNT`/`TRAVEL_SHARD_INDEX` round-robin
  sharding (the script has no internal concurrency; ~68s/group sequential).
  Shards skip combine/eval so a partial shard can't push a bogus score to the
  global CSV; `TRAVEL_AGGREGATE_ONLY=1` then merges shard usage + runs
  combine/eval once. 4-way sharding cut a 50-group config to ~7-8 min.
- `run_shards.ps1` (new): launches N shards, waits, aggregates. Loads `.env`
  and maps `OPENROUTER_API_KEY`→`OPENAI_API_KEY` (needed because
  `load_config` uses `os.environ.setdefault` and the memclaw config still has
  a literal `"<OPENAI_API_KEY>"` placeholder), and checks both ports are up.
- **Bug found + fixed:** shards died mid-run with `UnicodeEncodeError` on
  `☆` — with stdout redirected to a file, Windows Python encodes as
  cp1252 and the harness prints raw memory chunks/plan text. `run_shards.ps1`
  now sets `PYTHONIOENCODING=utf-8`.
- **Bug found + fixed:** on a resume run, shards whose groups were all already
  on disk did no work but still wrote all-zero `usage_stats_shard*.json`,
  **clobbering the real token numbers** from the run that did the work. Shards
  now track `groups_processed` and refuse to overwrite an existing file with a
  zero-work result; the aggregate line reports groups processed so per-group
  cost isn't mistakenly derived against the full scored set.

Caveat that still applies: token/cost totals only cover groups *executed in
that invocation*, which on a resume run is fewer than the scored set.

## MemoryArena math: results (2026-08-02) — consistent win, not significant

Full test split, both arms, same 40 papers / 354 subtasks,
`openai/gpt-4o-mini` via OpenRouter (`results/json/math/{memclaw,none}/`):

| arm | paper passrate | avg progress score | avg memory length |
|---|---|---|---|
| memclaw | **0.150** (6/40) | **11.77%** | 896 tok |
| none    | **0.050** (2/40) | **9.40%**  | 0 tok |

`none`'s memory length of exactly 0 confirms the null arm really ran
memory-free — a useful sanity check on the control.

**Unlike travel, all three metrics move together in memclaw's favour** — but
none reaches significance at this n:

| metric | memclaw | none | test | p |
|---|---|---|---|---|
| progress score (paired, 40 papers) | 11.77% | 9.40% | +2.37pp, 95% CI **[−1.14, +6.40]** | 0.247 |
| subtask correctness (354 subtasks) | 19 own-only | 10 own-only | McNemar exact | 0.136 |
| paper passrate (40 papers) | 6/40 | 2/40 | McNemar exact (5 vs 1 discordant) | 0.219 |

Per-paper wins: memclaw 9, none 7, **tied 24**.

**This is a different shape of result from travel.** Travel was a true null
(24/21 group split, p=0.448, gap *shrinking* as n grew). Math shows a
consistent directional effect across three independent metrics with p ≈
0.14–0.25 — that's underpowered, not absent. Do not report it as a win, and
do not dismiss it either.

**Careful with the headline metric:** eval.py defines `is_paper_correct` as
`logs[-1]['is_correct']` — **the final subtask only**, not all subtasks
(nothing scores all-correct: it's 0/40 for both arms under that reading).
So `overall_average_passrate` is "did the last subtask land", a single noisy
binary per paper. It is arguably the *right* memory metric (the last subtask
depends on the most accumulated context) but it has very little resolution.

**More data won't rescue this on MemoryArena.** Power analysis at the observed
effects: progress score needs **~213 papers** (have 40); subtask McNemar needs
**~79 discordant pairs ≈ 964 subtasks** at the observed 8.2% discordant rate
(have 354). `formal_reasoning_phys` is the only other formal-reasoning split
and adds just **20 papers / 86 subtasks** — pooling gets to 60 papers / 440
subtasks, still far short. Chasing significance by adding MemoryArena samples
is not viable.

The higher-value move is a **stronger agent model**: gpt-4o-mini leaves little
headroom (9-12% progress score), and memory should matter more when the agent
can actually use the recalled context. A larger effect needs far fewer samples.

### Follow-up diagnostics (2026-08-03)

- **Memory advantage grows with subtask position**, which is what a real memory
  mechanism should look like (later subtasks have more accumulated context):
  first third **+1.7pp**, middle **+2.9pp**, last **+3.1pp**.
- **But there is a gap at subtask 0, where memory is empty and there should be
  none**: memclaw 4/40 vs none 2/40. At n=40 that's well inside noise, but it
  means some of the aggregate gap may be a baseline offset (memclaw's prompt
  carries an empty `<memory_context>` wrapper, so the two arms' prompts are not
  byte-identical even with nothing stored) rather than memory itself. Treat the
  position trend as *weak supporting* evidence, not proof.
- **The judge is NOT a noise source** — an earlier worry, checked and dismissed.
  `math_env.judge` runs at `env_config.temperature`, which both configs set to
  **1.0**, so it looked stochastic. Re-judging 60 stored (answer, ground_truth)
  pairs 3x each produced **0/60 inconsistent verdicts at temperature 1.0** (and
  0/60 at 0.0). The yes/no equivalence task is confident enough that temperature
  doesn't bite. Don't bother "fixing" the judge temperature; the variance in
  these results is real task variance.
- **Model compatibility verified for the rerun**: `formal_reasoning_env/llm_backend.py`
  always passes `temperature` *and* `max_completion_tokens`, with none of the
  `gpt-5`-family special-casing the travel client has. Tested that exact call
  shape through OpenRouter against `openai/gpt-5-mini`, `deepseek/deepseek-v3.2`,
  `google/gemini-2.5-flash`, `anthropic/claude-haiku-4.5`, `openai/gpt-4.1-mini`
  — **all five succeed**, so no client patch is needed to swap the agent model.

### Additional eval bugs found + fixed (`formal_reasoning_env/eval.py`)

- `load_jsonl` opened result files with no encoding → cp1252 `UnicodeDecodeError`
  on math symbols, even though `run_math.py` writes them as UTF-8. Now opens
  `encoding='utf-8'` (same for the `all_results.json` write).
- `tokenizer.encode(log.get('memory_context',''))` crashed with `TypeError` on
  the no-memory arm: the key is *present but None*, so the `''` default never
  applies. Now `log.get('memory_context') or ''`. Without this no no-memory
  baseline can be scored at all.

## MemoryArena math: gpt-4.1 rerun (2026-08-04) — significant win

Followed through on the "Next action" item below: reran math with `agent.model_name`
swapped to `openai/gpt-4.1` in new configs `math_memclaw_gpt41.json` /
`math_none_gpt41.json` (output dir `./results/json/math_gpt41`), judge
(`env.env_config.model_name`) deliberately **left at `openai/gpt-4o-mini`**
in both arms — same reasoning as the earlier `math_*_gpt5mini.json` pair
(isolates the agent-model variable, keeps judge quality identical across
arms and comparable to the original baseline). Same 40 papers / 354
subtasks, full `run_math_shards.ps1` at 4 shards, both arms clean.

| arm | paper passrate | avg progress score | avg memory length |
|---|---|---|---|
| memclaw | **0.250** (10/40) | **23.95%** | 1422 tok |
| none    | **0.100** (4/40)  | **19.03%** | 0 tok |

**Unlike the gpt-4o-mini run, all three metrics now clear significance:**

| metric | memclaw | none | test | p |
|---|---|---|---|---|
| progress score (paired, 40 papers) | 23.95% | 19.03% | +4.92pp, 95% CI (bootstrap 20k) **[0.87, 9.04]** | perm test (20k) **0.024** |
| subtask correctness (354 subtasks) | 29 own-only | 14 own-only | McNemar exact | **0.031** |
| paper passrate (40 papers) | 10/40 | 4/40 | McNemar exact (6 vs 0 discordant) | **0.031** |

Per-paper wins: memclaw 15, none 6, tied 19 — a real skew, not the near-coin-flip
travel showed. `none`'s memory length of exactly 0 again confirms the control
ran memory-free. Full paired-stats script (bootstrap CI, permutation test,
both McNemar tests) is in the scratchpad from that session, not checked in —
rerun with the same method (`process_all_papers_for_method`/`get_passrate_at_k`
logic from `eval.py`, applied per-paper instead of aggregated) if this needs
reproducing.

**Effect roughly doubled vs gpt-4o-mini** (progress score +2.37pp → +4.92pp;
paper passrate gap 10pp → 15pp), consistent with the "gpt-4o-mini leaves no
headroom" diagnosis — a stronger agent model was the right lever, exactly as
predicted.

**Caveat — not three independent replications.** These are three correlated
tests off the same 40-paper run (paper passrate is literally the final-subtask
slice of subtask correctness; progress score is a different aggregation of
the same underlying per-subtask outcomes). Treat this as one converged result,
not triple confirmation. No multiple-comparisons correction applied — a strict
Bonferroni (α=0.0167 for 3 tests) would put progress-score and both McNemar
p-values right on the edge (0.024–0.031 vs 0.0167). Given the effect direction
and magnitude are consistent with (roughly 2x) the gpt-4o-mini directional
result rather than appearing out of nowhere, this reads as a real finding, but
say "significant at gpt-4.1, effect confirmed directionally at gpt-4o-mini" —
not "proven" — when citing it externally.

Everything under "Follow-up diagnostics (2026-08-03)" and "Additional eval
bugs found + fixed" below was done on the gpt-4o-mini data and hasn't been
re-checked at gpt-4.1 (subtask-position trend, judge-temperature-is-not-noise
finding, subtask-0 baseline-offset check). Worth re-running the subtask-position
breakdown at gpt-4.1 if pursuing this further — the earlier trend (+1.7pp →
+2.9pp → +3.1pp across thirds) was weak evidence at gpt-4o-mini; a cleaner
version might show up now that there's real signal to work with.

## MemoryArena math: mem0 arm result (2026-08-04) — mem0 ≈ none, memclaw beats both

The mem0 arm that was blocked on this machine's RAM (see "MemoryArena mem0 arm:
setup done, run blocked on this machine's RAM" below) was completed the same
day on a second machine, using the same `math_mem0_gpt41.json` config
(agent `openai/gpt-4.1`, judge `openai/gpt-4o-mini`, output dir
`./results/json/math_gpt41/mem0`, all 40 papers / 354 subtasks). Result files
came back as evidence and were reconciled into this checkout
(`json/math_gpt41/{memclaw,none,mem0}/` — per-paper `result.jsonl` logs plus
`all_results.json` summaries). **Note 2026-08-24: `math_gpt41/mem0/` is not on disk in this
checkout** — only `memclaw` and `none` are present. The numbers themselves
are almost certainly fine (this arm ran on the second machine, as the section
says, and the summary figures were reconciled here by hand), but the
per-paper logs evidently never made the trip, so from this checkout the mem0
arm cannot be re-scored, contamination-scanned, or re-analysed — only quoted.
The phys equivalent (`phys_gpt41/mem0/`, 20 papers) *is* present and clean.
Pull the math mem0 logs over from the second machine; see Next action item 4,
which now tracks every result in this state.** Recomputed all three arms' aggregates directly
from the per-paper logs to sanity-check against the numbers already recorded
above — they match (progress score +4.92pp, paper passrate McNemar p≈0.031,
subtask McNemar p≈0.031 for memclaw vs none, within rounding/bootstrap-seed
noise of the original run).

| arm | paper passrate | avg progress score | avg memory length |
|---|---|---|---|
| memclaw | **0.250** (10/40) | **23.95%** | 1422 tok |
| mem0    | **0.100** (4/40)  | **19.15%** | 319 tok |
| none    | **0.100** (4/40)  | **19.03%** | 0 tok |

**mem0 is statistically indistinguishable from no memory at all**, despite
storing something (319 tok/paper avg. vs memclaw's 1422, none's 0):

| comparison | metric | result | test | p |
|---|---|---|---|---|
| mem0 vs none | progress score (paired, 40 papers) | 19.15% vs 19.03%, **+0.12pp**, 95% CI [−2.93, +3.22] | perm test (20k) | **0.94** |
| mem0 vs none | paper passrate | 4/40 vs 4/40, **identical** | McNemar (1 vs 1 discordant) | **1.00** |
| mem0 vs none | subtask correctness (354 subtasks) | 13 vs 11 own-only | McNemar exact | **0.84** |

**memclaw beats mem0 by essentially the same margin it beats no-memory:**

| comparison | metric | result | test | p |
|---|---|---|---|---|
| memclaw vs mem0 | progress score (paired, 40 papers) | 23.95% vs 19.15%, **+4.81pp**, 95% CI [+1.13, +8.42] | perm test (20k) | **0.014** |
| memclaw vs mem0 | paper passrate | 10/40 vs 4/40 | McNemar (6 vs 0 discordant) | **0.031** |
| memclaw vs mem0 | subtask correctness (354 subtasks) | 26 vs 13 own-only | McNemar exact | 0.053 (not significant) |

Per-paper wins, memclaw vs mem0: memclaw 17, mem0 5, tied 18. Per-paper wins,
mem0 vs none: 8/8, tied 24 — a coin flip, consistent with the null reading.

**Interpretation:** mem0's async, fact-extraction-based ingestion (see the
"noted but not a blocker" caveat in the mem0 setup section below) evidently
isn't producing usable recall on this task at this timescale — it stores
~22% as much per paper as memclaw and it shows in outcomes. This has since
been **replicated on physics** (see "MemoryArena phys: mem0 arm result"
below), so the "mem0 ≈ none, memclaw beats both" reading now holds across
both formal-reasoning domains. Analysis script (bootstrap CI, permutation
test, both McNemar tests, computed directly from per-paper `result.jsonl`
logs) is in the scratchpad from this session, not checked in — same method as
the math/phys gpt-4.1 significance tests, applied to a third arm.

## MemoryArena phys: gpt-4.1 replication (2026-08-04) — stronger win, independent domain

Ran the `formal_reasoning_phys` split (the only other formal-reasoning domain,
20 papers / 86 subtasks) as a replication of the math gpt-4.1 result, same
setup: `phys_memclaw_gpt41.json` / `phys_none_gpt41.json` (new), agent
`openai/gpt-4.1`, judge `openai/gpt-4o-mini` (same reasoning as math — isolate
the agent-model variable), output `./results/json/phys_gpt41`. Both arms
clean, all 20 papers each.

| arm | paper passrate | avg progress score | avg memory length |
|---|---|---|---|
| memclaw | **0.350** (7/20) | **52.75%** | 1104 tok |
| none    | **0.050** (1/20) | **32.29%** | 0 tok |

**Bigger and cleaner than math, despite half the sample size:**

| metric | memclaw | none | test | p |
|---|---|---|---|---|
| progress score (paired, 20 papers) | 52.75% | 32.29% | +20.46pp, 95% CI (bootstrap 20k) **[8.58, 34.17]** | perm test (20k) **0.0036** |
| subtask correctness (86 subtasks) | 21 own-only | 3 own-only | McNemar exact | **0.0003** |
| paper passrate (20 papers) | 7/20 | 1/20 | McNemar exact (6 vs 0 discordant) | **0.031** |

Per-paper wins: memclaw **9**, none **0**, tied 11 — none did not win a single
paper. (Contamination scan run 2026-08-24, after the fact: `memclaw` has
**2/86 empty subtasks** from transient `APIConnectionError` retries — papers
`2309.15922` subtask 2 and `2507.7811` subtask 3 — while `none` and `mem0`
are clean at 0/86. Both are scored as failures for the arm that won, so the
recorded effect is if anything slightly understated. Too small to re-run;
noted for honesty.) All effects point the same direction as math and are considerably
larger (progress score gap 4.92pp → 20.46pp; subtask McNemar p 0.031 → 0.0003).

**This is the strongest evidence so far that memory matters when the agent
has headroom to use it.** Math and phys are not fully independent (same
env/judge infrastructure, same agent, same memory system) but they are
different papers, different physics content, and a different pass/fail
distribution — a genuine second data point, not a rerun of the same one.

Caveat carried over from math: three correlated tests off one run per domain,
not independent replications *within* a domain — but now there are two
domains agreeing in direction and both individually significant, which is
meaningfully stronger than either alone. Still applies: don't claim this
generalizes beyond formal-reasoning-style tasks at gpt-4.1-or-better agent
tiers without testing elsewhere (travel was a true null at gpt-4o-mini,
untested at gpt-4.1).

Pooled math+phys (60 papers / 440 subtasks) was not computed — the two
domains have different task structure and difficulty, so pooling progress
scores would need a domain fixed-effect, not a naive average. Worth doing if
this needs to go into an external-facing writeup; not done here.

## MemoryArena phys: mem0 arm result (2026-08-05) — replicates math, mem0 ≈ none

The last outstanding formal-reasoning arm. Ran on **this** machine after all
(not the second machine) at `-Shards 1` to avoid the OOM that killed the
4-shard math attempt — log
`results/math/logs/phys_mem0_gpt41-20260805-145924-shard0.log`, single shard,
~35 min wall clock for all 20 papers. Config `phys_mem0_gpt41.json` unchanged
(agent `openai/gpt-4.1`, judge `openai/gpt-4o-mini`, output
`./results/json/phys_gpt41/mem0`). All 20 papers / 86 subtasks present, no
failures. **This run happened 2026-08-05 but was never scored or recorded
until 2026-08-09** — it sat on disk as a completed-but-invisible result.

| arm | paper passrate | avg progress score | avg memory length |
|---|---|---|---|
| memclaw | **0.350** (7/20) | **52.75%** | 1104 tok |
| mem0    | **0.100** (2/20) | **36.26%** | 119 tok |
| none    | **0.050** (1/20) | **32.29%** | 0 tok |

**mem0 is again indistinguishable from no memory**, and again stores far less
than memclaw (119 tok/paper vs 1104 — an even wider ratio than math's 319 vs
1422):

| comparison | metric | result | test | p |
|---|---|---|---|---|
| mem0 vs none | progress score (paired, 20 papers) | 36.26% vs 32.29%, **+3.97pp**, 95% CI [−5.56, +14.14] | perm test (20k) | **0.45** |
| mem0 vs none | paper passrate | 2/20 vs 1/20 | McNemar (1 vs 0 discordant) | **1.00** |
| mem0 vs none | subtask correctness (86 subtasks) | 7 vs 3 own-only | McNemar exact | **0.34** |

**memclaw beats mem0, and by more than it beats none on math:**

| comparison | metric | result | test | p |
|---|---|---|---|---|
| memclaw vs mem0 | progress score (paired, 20 papers) | 52.75% vs 36.26%, **+16.49pp**, 95% CI [+6.42, +27.00] | perm test (20k) | **0.0067** |
| memclaw vs mem0 | subtask correctness (86 subtasks) | 20 vs 6 own-only | McNemar exact | **0.0094** |
| memclaw vs mem0 | paper passrate | 7/20 vs 2/20 | McNemar (5 vs 0 discordant) | 0.0625 (not significant) |

Per-paper wins, memclaw vs mem0: memclaw 10, mem0 2, tied 8. Per-paper wins,
mem0 vs none: 5/3, tied 12 — a coin flip, same shape as math.

**Note the passrate/subtask disagreement:** memclaw-vs-mem0 paper passrate
misses significance (p=0.0625) while subtask correctness clears it comfortably
(p=0.0094). That's the known resolution problem with `is_paper_correct` —
5-vs-0 discordant is the *best possible* p at n=5 under an exact binomial
test, so at 20 papers this metric simply cannot go below 0.0625 no matter how
lopsided the result. Read the subtask/progress-score numbers as the real
signal here; don't report the passrate p-value as evidence against the effect.

The memclaw-vs-none numbers recomputed in this pass match the 2026-08-04
values recorded above to within bootstrap-seed noise (+20.46pp, perm p=0.0038
vs 0.0036; subtask McNemar p=0.0003; passrate p=0.031) — an independent
reproduction of that result from the raw per-paper logs.

**The analysis script is now checked in** as
`scripts/paired_stats.py` in this repo (it had been rewritten from scratch
three times from scratchpad copies). Run it against any
`results/json/<domain>` directory holding arm subdirectories:
`python scripts/paired_stats.py <MemoryArena>/results/json/phys_gpt41` — it
loads every arm present and prints all three pairwise comparisons.

## MemoryArena phys: gemini-3.6-flash (2026-08-12) — replicates gpt-4.1, effect is larger

Second agent-model tier for the formal-reasoning track, run to test whether
the memclaw effect holds beyond gpt-4.1. Configs `phys_memclaw_gemini36.json` /
`phys_none_gemini36.json` (agent `google/gemini-3.6-flash`, judge left at
`openai/gpt-4o-mini` exactly as in the gpt-4.1 configs, output
`./results/json/phys_gemini36`). Both arms clean, all 20 papers / 86 subtasks,
0 failures, run sequentially at `-Shards 1` via `run_gemini36_phys.sh`.

| arm | paper passrate | avg progress score | avg memory length |
|---|---|---|---|
| memclaw | **0.550** (11/20) | **55.90%** | 671 tok |
| none    | **0.250** (5/20)  | **31.76%** | 0 tok |

| metric | memclaw | none | test | p |
|---|---|---|---|---|
| progress score (paired, 20 papers) | 55.90% | 31.76% | +24.14pp, 95% CI (bootstrap 20k) **[12.47, 36.22]** | perm test (20k) **0.0013** |
| subtask correctness (86 subtasks) | 26 own-only | 1 own-only | McNemar exact | **4.2e-07** |
| paper passrate (20 papers) | 11/20 | 5/20 | McNemar exact (6 vs 0 discordant) | **0.031** |

Per-paper wins: memclaw **12**, none **1**, tied 7.

**Every effect is larger than the gpt-4.1 phys run** (progress score +20.46pp →
+24.14pp; subtask McNemar p 0.0003 → 4.2e-07; the subtask split went from 21-vs-3
to **26-vs-1**). Both arms also scored higher in absolute terms than at gpt-4.1
(none 32.29% → 31.76% is flat, but memclaw 52.75% → 55.90%), so this is not
simply a stronger model lifting everything.

**This is the second agent model at which the effect is significant, and the
first evidence it is not a gpt-4.1 artifact.** Combined with the gpt-4.1 math
and phys results, memclaw-vs-none now holds across two domains and two agent
model families (OpenAI and Google).

Caveats carried forward unchanged: three correlated tests off one run (paper
passrate is the final-subtask slice of subtask correctness), so treat as one
converged result per domain, not three replications. The passrate metric again
sits at its floor — 6-vs-0 discordant cannot go below p=0.031 at n=20, so read
the subtask/progress-score numbers as the real signal.

**mem0 arm — originally blocked on account quota, now run and complete
(2026-08-20).** All 20 papers originally failed with `500` on
`/memory/wrap_user_prompt`; the memory-server traceback was
`mem0.exceptions.RateLimitError: Usage quota exceeded for this billing period.
event_type: SEARCH, quota_limit: 1000, quota_used: 1000,
quota_reset: 2026-09-01T00:00:00+00:00`. mem0 `add` calls still returned 200 —
only `search` was throttled — so the failure surfaced at recall time, and the
arm produced zero scoreable papers (`run_gemini36_phys.sh` reported
`papers=0`; note `run_math.py` still exits 0 in this case, so **always check
the paper count, not the exit code**). **Resolved 2026-08-19/20**: the mem0
account moved to a key/plan with working search (verified live), so
`run_gemini36_phys.sh` was rerun 2026-08-20 — `memclaw`/`none` skipped
(already 20/20 each), `mem0` completed all 20 papers cleanly (contamination
scan: 0/86 empty responses across all three arms).

| arm | paper passrate | avg progress score |
|---|---|---|
| memclaw | 0.550 (11/20) | 55.90% |
| mem0    | **0.350** (7/20) | **41.01%** |
| none    | 0.250 (5/20)  | 31.76% |

(memclaw/none numbers match the 2026-08-12 run exactly, as expected — same
data, no changes.)

**memclaw vs mem0 — memclaw wins, significant on progress score and subtask
correctness, not on paper passrate:**

| metric | memclaw | mem0 | test | p |
|---|---|---|---|---|
| progress score (paired, 20 papers) | 55.90% | 41.01% | +14.89pp, 95% CI **[2.64, 26.97]** | perm p **0.0346** |
| subtask correctness (86 subtasks) | 22 own-only | 4 own-only | McNemar exact | **0.0005** |
| paper passrate (20 papers) | 11/20 | 7/20 | McNemar exact (6 vs 2 discordant) | 0.289 (not significant — genuinely non-significant here, not just floor-limited like the gpt-4.1 phys mem0 result: discordance is 6-vs-2, not 5/6-vs-0) |

**mem0 vs no-memory — trending positive, not significant, and this is now a
second data point alongside math-gemini's similar (also non-significant)
trend:**

| metric | mem0 | none | test | p |
|---|---|---|---|---|
| progress score (paired, 20 papers) | 41.01% | 31.76% | +9.25pp, 95% CI [-1.58, 21.50] (crosses zero) | perm p 0.170 |
| subtask correctness (86 subtasks) | 9 own-only | 2 own-only | McNemar exact | 0.065 — closest to significance of any mem0-vs-none comparison run so far |
| paper passrate (20 papers) | 7/20 | 5/20 | McNemar exact (3 vs 1 discordant) | 0.625 |

**Pattern across both gemini-tier domains now: mem0 trends above no-memory
in both math (+3.74pp, p=0.076) and phys (+9.25pp, p=0.170), never
significant individually, but consistently directional — unlike gpt-4.1
where mem0≈none was a clean null in both domains (p=0.94, p=0.45).** This
reads as a genuine tier-dependent shift worth a note when reporting mem0
results, not just noise to ignore, but neither individual result clears
significance — don't report "mem0 beats no-memory at gemini tier" as
established, say "trending, not yet significant, consistent across two
domains."

Final balance after this run: **$48.40** account / $107.13 key-limit
headroom (2026-08-20).

## MemoryArena math: gemini-3.6-flash — ✅ complete (resumed + finished 2026-08-19)

**Update 2026-08-19: the resume completed cleanly and the result is in.**
After the account was topped up (see budget note below — landed in two
tranches, ending at **$60.83** account balance / $108.88 key-limit headroom
post-run), `bash run_gemini36_math.sh` was rerun and finished all three arms
at 40/40 papers each, `rc=0`. `scripts/check_result_contamination.py` confirms
all three live arms (`memclaw`, `none`, `mem0`) are **0/354 empty responses**
— the two contamination backup folders from 2026-08-18 (below) still flag as
contaminated, which is expected: they're quarantined evidence, not part of
the scored set.

| arm | paper passrate | avg progress score |
|---|---|---|
| memclaw | **0.350** (14/40) | **35.16%** |
| mem0    | **0.225** (9/40)  | **31.13%** |
| none    | **0.225** (9/40)  | **27.39%** |

**memclaw vs no-memory — significant, replicates gpt-4.1 math and both phys
tiers at this second model family:**

| metric | memclaw | none | test | p |
|---|---|---|---|---|
| progress score (paired, 40 papers) | 35.16% | 27.39% | +7.76pp, 95% CI **[3.92, 11.65]** | perm test (20k) **0.0006** |
| subtask correctness (354 subtasks) | 41 own-only | 15 own-only | McNemar exact | **0.0007** |
| paper passrate (40 papers) | 14/40 | 9/40 | McNemar exact (6 vs 1 discordant) | 0.125 (not significant — floor effect, same pattern as phys) |

Per-paper wins: memclaw 19, none 5, tied 16.

**mem0 vs no-memory — a different shape than gpt-4.1, worth flagging
honestly.** At gpt-4.1 (both domains), mem0 was flatly indistinguishable from
no-memory (p=0.94, p=0.45). Here it's closer to separating, though still not
significant: progress score +3.74pp, 95% CI **[-0.19, 7.70]** (just touches
zero), perm p=**0.076**. Per-paper wins mem0 17 / none 10 / tied 13 — less of
a coin flip than gpt-4.1's 8/8 splits. **Do not report this as "mem0≈none,
replicated a third time"** — the gpt-4.1 finding was clean; this one is
suggestive but not there. Small sample (n=40) and a single run — needs another
data point (e.g. the still-unrun phys mem0 gemini arm, see Next action) before
treating the difference between "mem0≈none at gpt-4.1" and "mem0 trending
above none at gemini" as a real tier-dependent effect rather than noise.

**memclaw vs mem0 — mixed, subtask-significant but not paper-level:**

| metric | memclaw | mem0 | test | p |
|---|---|---|---|---|
| progress score (paired, 40 papers) | 35.16% | 31.13% | -4.02pp reads as memclaw −(−4.02) = +4.02pp, 95% CI [-9.07, 1.03] | perm p=0.129 (not significant) |
| subtask correctness (354 subtasks) | 39 own-only | 22 own-only | McNemar exact | **0.040** |
| paper passrate (40 papers) | 14/40 | 9/40 | McNemar exact (5 vs 0 discordant) | 0.0625 — at its floor, same known resolution limit noted for phys gpt-4.1 |

**Bottom line: math now matches phys at the gemini-3.6-flash tier for the
memclaw-vs-none comparison — the effect holds across two domains and two
model families.** The mem0 comparison needs the phys gemini mem0 run (still
pending, see Next action) before drawing a firm tier-dependent conclusion.

**Run-script robustness fixes made while resuming (2026-08-19, `MemoryArena`,
uncommitted):** `run_gemini36_math.sh` failed twice when run directly from a
plain PowerShell prompt (not via this session's tooling) — (1) `.env` had
picked up CRLF line endings from a Windows editor, which broke `. ./.env`
sourcing (`$'\r': command not found`); fixed by stripping `\r` in place.
(2) `python` wasn't resolvable on PATH in that shell even after `$env:PATH`
edits — root cause was `bash` itself resolving to something other than Git
Bash (`where bash` found nothing, `-f`/`-x` tests on the known Python313 path
also failed under whatever that shell was — plausibly WSL's bash, where
`/c/...` paths don't exist). Fixed two ways: the script now resolves
`$PYTHON` itself (`command -v python`, falling back to the known Python313
absolute path) instead of assuming plain `python` works, and the reliable
invocation is to call Git Bash **by its full path** explicitly:
`& "C:\Program Files\Git\bin\bash.exe" run_gemini36_math.sh` — this is what
actually got the resume running.

---

Below is kept as historical record of how this got blocked, discovered
contaminated, and resumed — the section header used to read "⛔ STILL NOT
SCOREABLE"; that is resolved as of 2026-08-19 above.

Started 2026-08-12 right after the phys run above, same setup
(`math_memclaw_gemini36.json` / `math_none_gemini36.json`, output
`./results/json/math_gemini36`, `run_gemini36_math.sh` at `-Shards 1`).

**Blocker #1 (2026-08-12, resolved):** the OpenRouter *key's spending limit*
hit its $50 cap mid-run (`403 Key limit exceeded (total limit)`,
`limit_reset: None` — a lifetime cap, not a rolling window). Fixed by raising
the key's limit to $200 (confirmed via `/api/v1/key` on 2026-08-18:
`limit_remaining` was $142.85 that day).

**Blocker #2 (found 2026-08-18, much worse — silently corrupted data, not a
clean failure):** raising the key's *limit* doesn't add funds to the
*account*. The account's actual funded credit balance (`/api/v1/credits`,
`total_credits - total_usage`) ran dry mid-run on 2026-08-13, and **every
subtask that hit the resulting 402 was silently written as a normal
"completed" result with an empty response** instead of failing the paper —
see `_reasoning_with_errors` in `agent/math.py`, which caught the 402 like
any other exception, retried it 3x (all 3 guaranteed to fail), and returned
`("", errors)` on exhaustion. `run_math.py`'s per-paper failure tracking never
saw an exception, so the 2026-08-13 run logged "40 attempted, 0 failed" for
both `none` and `memclaw` and looked completely clean. It sat unnoticed for
5 days.

**Damage, discovered 2026-08-18 while running the mem0 arm at this tier:**

| arm | subtasks empty (402) | papers affected |
|---|---|---|
| `none` (2026-08-13 run) | **354/354 — 100%** | 40/40, every paper |
| `memclaw` (2026-08-13 run) | 137/354 (39%) | 16/40 |
| `mem0` (run 2026-08-18, after the key-limit fix) | 0/354 — clean | 0/40 |

A same-day repair attempt (delete contaminated papers, re-run) was itself
interrupted by the *same* balance exhaustion recurring mid-run — confirmed via
`/api/v1/credits` showing only **$14.36 remaining**, not enough to safely
finish the ~52 remaining papers (~$16-20 estimated). The repair run and its
wrapper process were killed immediately, and a follow-up scan (see tooling
below) caught 3 more subtasks with genuine transient `APIConnectionError`
empty responses inside what had looked like the "already clean" 24 memclaw
papers — those were pulled too. Contaminated papers were moved, not deleted,
to `results/json/math_gemini36/_contaminated_402_backup_20260818/` (kept as
evidence, excluded from scoring).

**Verified-clean state on disk as of 2026-08-18** (superseded — see the
completion note at the top of this section for the 2026-08-19 finish):

| arm | clean papers | still needed |
|---|---|---|
| memclaw | 21/40 | 19 |
| none | 4/40 | 36 |
| mem0 | 40/40 | 0 — fully done, clean |

Was blocked on a real OpenRouter account top-up (not a key-limit change —
already confirmed sufficient). Resolved 2026-08-19: account funded, resume
run completed all remaining papers in both arms cleanly.

### Safeguards added 2026-08-18 so this class of bug can't recur silently

1. **`agent/math.py`: `UnrecoverableAPIError`.** `_reasoning_with_errors` now
   inspects `getattr(e, "status_code", None)` on every caught exception; a
   401/402/403 raises immediately (no wasted retries — they're account-level,
   not per-call flakiness) instead of being swallowed as an empty response
   after 3 attempts. Genuinely transient errors (timeouts, connection errors,
   429s — anything without a status_code in {401,402,403}) still retry exactly
   as before; verified no regression.
2. **`run_math.py`: aborts the whole run on `UnrecoverableAPIError`** instead
   of logging one paper as failed and continuing to the next — an account-level
   failure dooms every remaining paper identically, so continuing just burns
   more of the (already-exhausted) budget on guaranteed failures.
3. **`scripts/check_openrouter_balance.py`** — pre-flight check, run before
   any paid run starts. Checks *both* the key's spending-limit headroom
   (`/api/v1/key`) *and* the account's actual funded credit balance
   (`/api/v1/credits`) — the two are independent and this bug happened
   because only the first was ever checked. Wired into
   `run_gemini36_math.sh`, `run_gemini36_phys.sh`, and `run_math_shards.ps1`
   as a hard precondition (`--min-usd 15`, exits before spending anything if
   either check fails).
4. **`scripts/check_result_contamination.py`** — scans any arm directory (or
   directory of arm directories) for empty-response subtasks and classifies
   the error signature (402/401/403/rate-limit/timeout/unknown). This is the
   check that should have caught the 2026-08-13 `none` arm on day one instead
   of 5 days later — run it on any result set before feeding it to
   `paired_stats.py`. Example: `python scripts/check_result_contamination.py
   results/json/math_gemini36`.

**Process lesson, not just a tooling one:** "N attempted, 0 failed" in a
harness log is not evidence of valid data — it only means every subtask wrote
*a* line, not a *correct* line. Run the contamination scanner as a standard
step before trusting any new result, the same way `paired_stats.py` is now a
standard step before citing a comparison.

Budget note for planning the resume: the gemini phys run (2 arms × 86
subtasks) plus the original 12 math memclaw papers together cost about **$13**
on 2026-08-12. A full math pair (2 arms × 354 subtasks) should be budgeted at
roughly **$25-30** in clean conditions, but the 2026-08-18 session burned
budget on retries against a dead account without producing usable data, so
budget for some waste margin on top of that when funds are restored — the
earlier per-model estimates for `anthropic/claude-opus-5` (~$125-145) and
`openai/gpt-5.6-sol` (~$145) assumed a 3-arm × 2-domain sweep in clean
conditions and should be treated as optimistic floors, not ceilings.

## KNOWN HARNESS ISSUE: the agent tool loop has never run (found 2026-08-12)

**Every formal-reasoning result recorded above was produced by a single-shot
reasoner, not the tool-using agent the harness intends.**

`agent/math.py:_act_with_tools` builds its *own* `OpenAI` client from
`os.getenv("OPENAI_API_KEY")` / `os.getenv("OPENAI_BASE_URL")` — it ignores
the `agent.base_url` set in the config. `OPENAI_BASE_URL` is never exported by
`run_math_shards.ps1` (or any of the run scripts), so the tool-loop client
points at `api.openai.com` while holding an OpenRouter `sk-or-v1-...` key. It
401s on the first call. `act()` catches the exception and silently falls back
to `_reasoning_with_errors()`, which uses `self.llm_backend` — correctly
configured with the OpenRouter base_url from the config, hence a plausible
answer and no visible failure.

Verified: **708 of 708** stored subtasks across `results/json/math_gpt41/` and
`results/json/phys_gpt41/` carry
`"error": "tool loop failed: AuthenticationError: Error code: 401 - Incorrect
API key provided: sk-or-v1***"`. Not one subtask used the tool loop. The
gemini-3.6-flash runs (2026-08-12) show the same, deliberately — see below.

**This does not invalidate the recorded comparisons.** Every arm in every
domain hit the identical code path, so memclaw-vs-mem0-vs-none remains a fair
paired comparison and the significance tests stand. What it does mean:

- the agent is weaker than the harness advertises — no `coding` tool, no
  multi-turn self-correction, one reasoning call per subtask;
- absolute scores (progress score, passrate) are **floors**, not the harness's
  true capability;
- `MATH_AGENT_MAX_TOOL_ITERATIONS` has been dead config all along.

**Deliberately left unfixed** so far: fixing it changes the agent's code path,
which would make new runs incomparable to every number recorded above. New
model tiers are being added on the *broken* path on purpose, to keep agent
model the only changed variable. If it is ever fixed, the fix is one line
(pass the config's `base_url` into the client in `_act_with_tools`, or export
`OPENAI_BASE_URL` in the run scripts) — but it requires re-running gpt-4.1 as
well to re-establish the baseline.

## MemoryArena opus5 / gpt-5.6-sol: the failed August attempts (2026-08-23/24)

**Superseded for opus5 — phys landed 2026-08-27, see "MemoryArena phys: claude-opus-5" above.** Kept for the cost/cause record and the fixes it produced, all of which the successful run depended on.

**Status: no scores. Nothing from this tier is citable.** Recorded here for
cost and cause, not for numbers — the only paired-clean data that survives is
5 phys papers, far below anything this file's method note would accept.

**What is on disk after the 2026-08-24 cleanup:**

| dir | live arms | note |
|---|---|---|
| `phys_opus5` | memclaw 15/20, none 5/20 — both scan 0% empty | 5 papers clean in **both** arms (the only paired data) |
| `math_opus5` | none | 40+40 papers quarantined, 100% 402-empty |
| `math_gpt56sol` | none | 14 papers quarantined, 100% 402-empty |
| `phys_gpt56sol` | none | never ran |

Quarantined evidence lives in `_contaminated_402_backup_20260823/` and
`_contaminated_empty_backup_20260824/` per domain — kept, excluded from
scoring, never delete without reading the sections above first.

**Cost: $46.79** on the key between the 2026-08-20 snapshot ($92.87 lifetime
used) and 2026-08-24 ($139.66). Split: ~$19.97 on 08-23 (0 usable papers),
$26.82 on 08-24 (exact, from `usage_daily`), of which **$23.74** was the
12:58 phys run. Roughly **75% of that run went to calls that returned
nothing** — see cause below. Account balance ran to **-$0.17**; a top-up is
step 0 before anything here resumes.

### Cause: empty completions from a reasoning model, retried and swallowed

A second instance of the 2026-08-18 contamination class, from a different
cause. `llm_backend.py`'s `OpenAIBackend.chat` called `.strip()` directly on
`message.content`, which is **`None`** (not `""`) when a reasoning model
spends its whole `max_completion_tokens` budget on reasoning tokens before
emitting any content. Opus 5 does this routinely at `max_tokens: 8192` — the
value every config carried, chosen back when the agent was gpt-4o-mini and
8192 was a generous *answer* budget. The resulting `AttributeError` was
retried 3x (deterministic, so all three re-billed the identical failure at
the full 8192-token output price, ~$0.20/call on Opus 5) and then written as
a normal "completed" subtask with an empty response. Damage: `phys_opus5`
memclaw 16/86 empty (18.6%), none 25/75 (33.3%) — note the arms were hit
**unevenly**, which would have skewed the comparison toward memclaw had it
been scored.

The 08-18 safeguard did not catch it: that guard was scoped to status codes
`{401, 402, 403}`, i.e. the one *cause* that had bitten us, while
`check_result_contamination.py` was already written against the general
*symptom* (any empty response). Guard the symptom, not the cause.

### Fixes made 2026-08-24 (in `MemoryArena`, uncommitted)

1. **`llm_backend.py`**: `(response.choices[0].message.content or "").strip()`
   — no more `AttributeError` on `None` content.
2. **`agent/math.py`**: `_reasoning_with_errors` now raises
   `UnrecoverableAPIError` when *every* retry came back empty, regardless of
   cause, instead of returning `("", errors)` to be written as a completed
   subtask. Paper-level resume makes re-running cheap once the cause is fixed.
3. **`run_math.py`**: an abort sets a flag, logs `All papers ABORTED (...)`
   instead of `completed`, and raises `SystemExit(1)`. Previously the 08-18
   safeguard aborted the run correctly but the process still exited **0**, so
   `run_opus5_phys.sh` printed `rc=0 papers=17` for a run that had hard-
   aborted on a 402 three papers from the end.
4. **All four run wrappers** (`run_{opus5,gpt56sol}_{math,phys}.sh`): each arm
   is scanned with `check_result_contamination.py` the moment it finishes, and
   a contaminated *or* aborted arm stops the script **before the next arm
   spends anything**. On 08-24 this would have halted at 13:18 and saved the
   entire `none` arm's spend.
5. **`agent.max_tokens` 8192 → 32768** in all eight opus5/gpt56sol configs.
   Judge left at 4096/`gpt-4o-mini`, so agent model stays the only variable.
6. **`test_empty_completion.py`** (new, repo root): self-check for 1 and 2.

**~~Still unpatched (found 2026-08-26)~~ — FIXED, verified 2026-09-08.** The
note below claimed `OpenRouterBackend.chat` still carried the unguarded
`response.choices[0].message.content.strip()`. It does not: both call sites are
`(response.choices[0].message.content or "").strip()` (`llm_backend.py:117` and
`:233`). Nothing to do here.

**Attribution, for the record:** the `.strip()`-on-`None` bug is *upstream's* —
it is line 81 of `llm_backend.py` at `HEAD`, untouched by us, as is the
retry-3x-then-return-`("", errors)` loop in `agent/math.py`. It was latent, not
broken: non-reasoning models always return content, and upstream never ran a
reasoning model through it. **The trigger and the cost were ours** — `max_tokens:
8192` sat in our opus5 configs, a value chosen for gpt-4o-mini and never
revisited for a model that spends its budget thinking. And our own 2026-08-18
safeguard, written *specifically* for silently-empty subtasks, was scoped to
`status_code in {401,402,403}` — the cause that had bitten us — so an
`AttributeError` walked straight past it. Right instinct, one level too
specific.

### Root cause found 2026-08-26: Opus 5 needs extended thinking OFF

The contingency this file predicted ("if the canary aborts, 32768 was still not
enough and Opus 5 needs a `reasoning: {effort}` param") turned out to be the
right diagnosis with a simpler fix: **Opus 5 emits no content at all unless
extended thinking is disabled**. `run_opus5_subset.sh` (new, another session)
exports `MATH_DISABLE_REASONING=1`, and a 4-paper paired phys subset ran
**0/36 and 0/13 empty responses — completely clean, 0 failures**. The failure
that burned $46.79 in August is solved; the pipeline runs end to end.

`run_opus5_subset.sh <phys|math> <shard_count>` shards round-robin over a
deterministic paper order so the **same** subset lands in both arms and the pair
stays valid. It is explicitly **not a citable result** at these n — it exists to
prove the pipeline and measure real per-paper cost. Do not compute a gap from it.

Results from the earlier reasoning-ON attempts were quarantined 2026-08-26 to
`phys_opus5/_reasoning_on_backup_20260826/` (16 memclaw + 5 none papers). They
scan **clean** (0/66, 0/15) — they are not contaminated, just run under a
different agent configuration and therefore not comparable with the new arm.
Correct call; do not merge them back in.

OpenRouter was topped up 2026-08-26: **$16.22 account / $36.08 key headroom**.

**Do not trust `papers=N` or `rc=0` from a wrapper.** `papers=` is
`ls -d ... | wc -l` — directories on disk, not clean ones. The contamination
scan is the only signal that means anything.

### Before resuming

Top up (**$200** suggested; ~$115-140 estimated for both models × both
domains at 2 arms), then run **one paper as a canary** and scan it before
committing to the ~$70-85 math run. If the canary aborts with `empty response
after 3 attempts`, 32768 was still not enough and Opus 5 needs a
`reasoning: {effort}` param instead — learned for pennies. Resume order:
finish phys opus5 (5 memclaw + 15 none papers) → score → math opus5 → phys
gpt56sol → math gpt56sol. Live pricing 2026-08-24: Opus 5 $5/$25 per M,
gpt-5.6-sol $2/$10, gemini-3.6-flash $0.75/$3.75, gpt-4o-mini $0.15/$0.60 —
Opus 5 is **6.7x** gemini on output.

**Scope call: 2 arms only (memclaw/none) at these tiers.** No mem0 configs
exist for opus5/gpt56sol and a third arm is +50% on the most expensive models
available; gpt-4.1 and gemini already carry the mem0 comparison.

## MemoryArena phys: claude-opus-5 (2026-08-27) — first real Opus score, and it breaks the "erosion" story

The tier that produced nothing but bills in August finally landed. Run on
**OpenRouter** with `MATH_DISABLE_REASONING=1` (the fix found 2026-08-26 —
Opus 5 emits no content at all with extended thinking on), configs
`phys_{memclaw,none}_opus5.json` unchanged otherwise, judge **`openai/gpt-4o-mini`**
— i.e. the *same ruler as gpt-4.1 and gemini-3.6-flash*, which turns out to
matter a great deal (see below). Both arms scan clean: memclaw 0/70, none 0/86.

> ✅ **COMPLETED TO 20/20 on 2026-09-13.** The three missing memclaw papers
> were re-run (they had failed on Caura `caura_write` 500s in August, leaving
> no directory, so the resume picked up exactly those three). **Both arms now
> scan clean at 0/86.** The 17-paper figures below are superseded by the
> 20-paper numbers here, and they were representative — the gap barely moved.

| arm | paper passrate | avg progress score |
|---|---|---|
| memclaw | **13/20** | **52.64%** |
| none | 4/20 | 35.76% |

| metric | result | test | p |
|---|---|---|---|
| progress score (paired, 20 papers) | +16.88pp, 95% CI **[0.62, 33.96]** | perm (20k) | 0.0699 (not significant) |
| paper passrate (20 papers) | 13/20 vs 4/20, **9 vs 0 discordant** | McNemar exact | **0.0039** ✅ |
| subtask correctness (86 subtasks) | 26 own-only vs 5 | McNemar exact | **0.00019** ✅ |

Per-paper wins: memclaw **10**, none **4**, tied 6.

**Adding the three papers changed nothing material**: +17.40pp → **+16.88pp**,
subtask p=0.00018 → 0.00019, and paper passrate *strengthened* (p=0.0078 →
**0.0039**). Progress score stays non-significant at n=20. So the August
result was not distorted by the papers Caura's backend ate.

**Superseded 17-paper figures, kept for the record:** memclaw 11/17 / 52.94%,
none 3/17 / 35.54%, +17.40pp (perm p=0.085), passrate 8-vs-0 p=0.0078,
subtask 24-vs-4 p=0.00018 over 70 subtasks, wins 9-3-5.

**The paper passrate is genuinely significant here, which is rare** — that
metric normally sits at its exact-binomial floor (see the phys gpt-4.1 mem0
note). 8-vs-0 discordant at n=17 clears it on merit, not on resolution.

Note the CI/permutation disagreement on progress score: the bootstrap CI
excludes zero ([0.25, 35.78]) while the permutation test gives p=0.085. At
n=17 with a wide spread these can disagree; **report the permutation p and
call progress score non-significant**, consistent with how every other tier
here is reported.

### This is the tier that undercuts the "headroom in reverse" reading

| tier (phys) | memclaw | none | gap | perm p | judge |
|---|---|---|---|---|---|
| gpt-4.1 | 52.75% | 32.29% | +20.46pp | 0.0036 | gpt-4o-mini |
| gemini-3.6-flash | 55.90% | 31.76% | +24.14pp | 0.0013 | gpt-4o-mini |
| **claude-opus-5** | **52.64%** | **35.76%** | **+16.88pp** | 0.070 | **gpt-4o-mini** |
| gpt-5.6-sol | 62.71% | **53.64%** | +9.07pp | 0.204 | **gpt-5-mini** |

Opus 5 is a frontier model — at or above gpt-5.6-sol — and the effect there is
**large (+16.88pp), not compressed.** More decisive is the `none` column: every
tier scored by `gpt-4o-mini` lands at **32-36%**, and the sole outlier at
53.64% is the sole tier scored by `gpt-5-mini`.

**This is direct evidence for the judge-leniency confound that was previously
only an argument** (see "The judge-leniency confound is NOT symmetric" in the
math gpt-5.6-sol section). The phys gpt-5.6-sol section's speculation — "a
stronger agent recovers from context that weaker agents needed memory to
supply", the *headroom argument running in reverse* — now looks much more like
a **measurement artifact of the swapped judge** than a capability finding.

**Consequences, act on these:**
- **Do not cite "the memclaw effect erodes as agent strength rises."** Four
  tiers on phys, three of them on one ruler, show +17 to +24pp with no
  downward trend in agent strength. Only the differently-judged tier is low.
- ✅ **DONE 2026-08-27, scored 2026-09-01.** The re-judge ran and confirmed
  this inference as a measurement: on the common `gpt-4o-mini` ruler phys
  `none` drops 53.64% → **47.81%** and the gap grows +9.07 → **+12.37pp**;
  math goes +4.16 → **+7.02pp, p=0.0054 (now significant)**. See
  "gpt-5.6-sol RE-JUDGED on the common ruler" below.
- The gpt-5.6-sol tier's *within-tier* comparisons remain valid (all arms share
  their judge); it is the cross-tier absolute numbers that are suspect.

### Caveats

- ~~**17 papers, not 20.**~~ **RESOLVED 2026-09-13 — now 20/20, see the note at the top of this section.** Three memclaw papers had failed on **Caura's own storage
  backend** returning `500` on `caura_write`
  (`prod-memclaw-core-storage-reader-...run.app/api/v1/storage/agents/...`),
  surfacing locally as `500` on `/memory/add`. Not our harness, not the LLM,
  not OpenRouter. Each failure carried a distinct `agent_id`, so it reads as
  transient backend flakiness rather than one poisoned record; two of the
  original five recovered on the accidental second pass (the known
  double-`main()` quirk in `run_math.py` acting as a retry). **First time
  Caura's own service has been the failure point in any run in this project.**
  Failed papers leave no directory, so a re-run retries exactly those three
  and skips the other 17 — cheap, once there is budget.
- The `none` arm is 20/20 and clean; `paired_stats.py` scores on the 17 papers
  in common, so the pairing is valid, just smaller.
- **Cost $15.29** (balance $19.78 → $4.49), above the $10-11 projection that
  justified lowering the run gate from `--min-usd 20` to `12`. The gate was not
  wrong to be lowered — the run did fit — but the estimate was optimistic;
  budget Opus phys at ~$15 for the remaining-29-papers shape, more for a full 40.

### Budget state after this run — everything else is blocked

**Measured 2026-09-01: $12.52 account / $0.70 key-limit headroom.** (Was $4.49
/ $0.81 right after the Opus run; the account has since been topped up, the key
limit has not been raised.) **The key limit is the binding constraint** — the
account can hold any amount and the key still only spends $0.70 more, so
raising the key's limit in the OpenRouter dashboard is step 0 for everything
below. The ~$0.20 re-judge squeezed in before this and is ✅ done. Still
blocked: the 3 missing Opus papers, the math mem0 arm (stopped at 15/40, clean,
resumable), and any Opus math run. Azure is not an alternative — that subscription's free credit
expired 2026-08-27 and all calls 401 (resource slated for deletion 2026-09-25
unless upgraded; **no benchmark data is at risk, all results are local files**).

## gpt-5.6-sol RE-JUDGED on the common ruler (2026-08-27) — the compression was largely a judge artifact

**This section supersedes the absolute numbers and the "baseline catches up"
reading in the two gpt-5.6-sol sections below.** The re-judge those sections
called for was run 2026-08-27 20:00 by `scripts/rejudge.py` (new, in
`MemoryArena`) and scored 2026-09-01.

Every stored `(query, response, ground_truth)` triple from both gpt-5.6-sol
domains was re-scored with **`openai/gpt-4o-mini` via OpenRouter** — the same
judge as gpt-4.1, gemini-3.6-flash and claude-opus-5 — so all five tiers now
share one ruler. No agent re-run: the expensive half was already on disk.
Verdicts went to sidecar directories (`results/json/{math,phys}_gpt56sol_rejudged/`),
leaving the gpt-5-mini verdicts intact as evidence.

| domain | rows | judged | →correct | →wrong | unjudged |
|---|---|---|---|---|---|
| math | 824 | 824 | 74 | 53 | 0 |
| phys | 258 | 258 | 16 | 27 | 0 |

### memclaw vs none — the gap widens in BOTH domains

| domain | judge | memclaw | none | gap | perm p | subtask McNemar |
|---|---|---|---|---|---|---|
| math | gpt-5-mini (old) | 37.45% | 33.29% | +4.16pp | 0.141 | 0.020 |
| math | **gpt-4o-mini (re-judged)** | **41.62%** | **34.60%** | **+7.02pp** | **0.0054** ✅ | **0.0011** ✅ |
| phys | gpt-5-mini (old) | 62.71% | 53.64% | +9.07pp | 0.204 | 0.024 |
| phys | **gpt-4o-mini (re-judged)** | **60.18%** | **47.81%** | **+12.37pp** | 0.091 | **0.043** ✅ |

Re-judged detail — math (40 papers / 354 subtasks), 95% CI [2.42, 11.74]pp,
per-paper wins memclaw 21 / none 6 / tied 13; paper passrate 13/40 vs 9/40
(discordant 6 vs 2, McNemar p=0.289, still floor-limited). Phys (20 papers /
86 subtasks), 95% CI [-0.46, 25.46]pp, wins memclaw 9 / none 4 / tied 7;
paper passrate 12/20 vs 7/20 (discordant 8 vs 3, p=0.227).

**Math flips from non-significant to p=0.0054 on the paper-level progress
score.** Phys's progress score is still non-significant at n=20 (p=0.091) but
its gap grew by a third. Subtask correctness clears in both, as it did before.

### The judge swap was NOT a uniform leniency shift — record this honestly

The earlier "gpt-5-mini is ~6pp more lenient" figure came from
`scripts/judge_agreement.py` on **`phys_gpt41`** pairs, and it does not
generalize: re-judging moved verdicts *both* directions and by a different net
in each domain. Under `gpt-4o-mini` **both math arms rose** (memclaw +4.17pp,
none +1.31pp) while **both phys arms fell** (memclaw −2.53pp, none −5.83pp).

So the correct claim is not "the old judge was lenient and inflated the
baseline". It is narrower and still decisive: **on a single consistent ruler
the memclaw-vs-none gap is larger in both domains than the swapped-judge
numbers showed, and in math it becomes significant.** The weaker arm moved more
than memclaw in both domains — which is the asymmetry the confound section
below predicted, just not in a single direction.

### Consequences — act on these

- **The "headroom in reverse" / "effect erodes as agents get stronger" reading
  is dead.** It rested on phys's `none` arm reaching 53.64%; on the common
  ruler that is **47.81%**. Combined with claude-opus-5's +16.88pp at a
  frontier model, there is no downward trend in agent strength to cite.
- **Quote the re-judged numbers for gpt-5.6-sol from now on**, and only those,
  in any cross-tier table. The gpt-5-mini figures stay as evidence of the
  confound, not as results.
- The tier's other two deviations are unchanged and still apply: **agent
  temperature 1.0** (the model rejects 0.0) inflates variance relative to every
  earlier tier, and the arms ran on Azure (memclaw/none) vs OpenRouter (mem0).

### mem0 at this tier, re-judged — read with care

| domain | mem0 | memclaw | none | mem0 vs none | mem0 vs none subtask |
|---|---|---|---|---|---|
| phys (20 papers) | 51.86% | 60.18% | 47.81% | +4.06pp, p=0.388 | 10 vs 11 own-only, **p=1.0** |
| math (**15 papers only**) | 43.94% | 45.94% | 38.15% | +5.78pp, p=0.126 | 10 vs 3 own-only, p=0.092 |

Phys re-judged keeps the 2026-08-27 finding intact: **mem0 vs none is an exact
coin flip on subtask correctness (p=1.0)** while **memclaw beats mem0
significantly on the same metric (7 vs 20 own-only, p=0.019)**. The strong
baseline does not lift mem0.

**The math mem0 row is a 15/40-paper slice** — that arm stopped at 15 papers
(clean, resumable) and its memclaw/none columns above are recomputed on those
same 15 papers, so they do NOT match the 40-paper figures in the table further
up. Do not quote the math mem0 row beside the 40-paper numbers. Finish the arm
before citing it.

### Cite as

*At gpt-5.6-sol, scored on the same `gpt-4o-mini` judge as every other tier,
memclaw beats no-memory by +7.02pp on math (p=0.0054, subtask p=0.0011) and
+12.37pp on phys (progress score p=0.091 at n=20, subtask p=0.043). The
apparent compression at this tier in the originally-reported numbers was
substantially an artifact of the swapped `gpt-5-mini` judge.*

## MemoryArena phys: gpt-5.6-sol (2026-08-25) — weakest effect yet, strong baseline

> ⚠️ **SUPERSEDED for absolute numbers and interpretation** by "gpt-5.6-sol
> RE-JUDGED on the common ruler" above. On the shared `gpt-4o-mini` judge this
> tier reads memclaw 60.18% / none **47.81%**, gap **+12.37pp** — not the
> 62.71/53.64 and +9.07pp below. The "baseline catches up" reading here is an
> artifact. Kept for the run record and the caveats, which still apply.

Third agent-model tier, run on Azure (see the Azure section below for the
three deviations this tier carries — they matter for reading these numbers).
Both arms clean: 20/20 papers each, **0/86 empty responses in both**, no
aborts, no judge errors. Configs `phys_{memclaw,none}_gpt56sol.json`,
output `./results/json/phys_gpt56sol`, sequential.

| arm | paper passrate | avg progress score | avg memory |
|---|---|---|---|
| memclaw | **0.450** (9/20) | **62.71%** | 956 chars/paper |
| none    | **0.350** (7/20) | **53.64%** | 0 (control verified) |

| metric | result | test | p |
|---|---|---|---|
| progress score (paired, 20 papers) | +9.07pp, 95% CI **[-3.06, 22.42]** — crosses zero | perm (20k) | **0.204** (not significant) |
| subtask correctness (86 subtasks) | 21 own-only vs 8 | McNemar exact | **0.024** ✅ |
| paper passrate (20 papers) | 9/20 vs 7/20 (5 vs 3 discordant) | McNemar exact | 0.727 (not significant) |

Per-paper wins: memclaw 6, none 4, **tied 10**.

**Only one of three metrics clears significance**, and it is the one with the
most resolution (86 subtask observations vs 20 paper observations). Note the
paper passrate is genuinely non-significant here, not floor-limited as at
earlier tiers: discordance is 5-vs-3, not 6-vs-0.

### Compared across phys tiers — the `none` column is the story

| tier | memclaw | none | diff | perm p | wins |
|---|---|---|---|---|---|
| gpt-4.1 | 52.75% | 32.29% | +20.46pp | 0.0036 | 9-0-11 |
| gemini-3.6-flash | 55.90% | 31.76% | +24.14pp | 0.0013 | 12-1-7 |
| **gpt-5.6-sol** | 62.71% | **53.64%** | **+9.07pp** | **0.204** | **6-4-10** |

The no-memory baseline jumps from ~32% at both earlier tiers to **53.64%**.
memclaw improved too (55.90 → 62.71) but far less, so the gap compressed.
~~Reading: a stronger agent recovers from context that weaker agents needed
memory to supply — **the headroom argument running in reverse**.~~
**WRONG — withdrawn 2026-09-01.** On the common judge this baseline is 47.81%,
not 53.64%, and the gap is +12.37pp. The jump was mostly the judge swap.
Original speculation kept below, struck through, so the reasoning error stays
visible: gpt-4o-mini
was too weak to *use* memory (2026-08-02); gpt-5.6-sol is strong enough to
*need* it less. If that holds, the memclaw effect is not monotonic in agent
strength — it peaks at mid-tier models and erodes as the baseline catches up.
**One domain at one tier is not enough to claim that.** The math run at this
tier is the test: 354 subtasks has the power to resolve a +9pp effect that
20 papers cannot. **ANSWERED 2026-08-26 — and it did not replicate.** Math's
gap barely moved from gpt-4.1 (+4.92pp → +4.16pp) with both arms rising
together, rather than the baseline closing on memclaw as it did here. Treat
the reversal reading below as phys-only and unconfirmed; see "MemoryArena
math: gpt-5.6-sol" for the revised interpretation.

### Caveats — all cut against over-reading this

- **The `gpt-5-mini` judge grades ~6pp more leniently** than the `gpt-4o-mini`
  judge used at every other tier, inflating both arms' absolute numbers. It
  cannot explain the *difference* (both arms share the judge), so +9.07pp
  stands as a within-tier measure — but **62.71% / 53.64% must not go in the
  cross-tier table above without this caveat attached.** Some of the apparent
  baseline jump may be judge leniency rather than agent capability.
- **Agent temperature is 1.0, not 0.0** (the model rejects 0.0). More sampling
  variance widens the CI and makes non-significance easier to reach at n=20.
- ~~No mem0 arm at this tier (scope decision). The "does a strong baseline
  compress mem0 too" question is open.~~ **Answered 2026-08-27 — see below.**

### mem0 arm run 2026-08-27 — the strong baseline does NOT lift mem0

The arm this section called for. Ran on **OpenRouter, not Azure** (the Foundry
subscription's free credit ran out that morning and every call 401s; config
`phys_mem0_gpt56sol_or.json`, agent `openai/gpt-5.6-sol`, judge
`openai/gpt-5-mini` — same models, so the judge matches the ruler the memclaw
and none arms were scored with). 20/20 papers, **0/86 empty responses**,
**$1.55** total.

| arm | progress score | paper passrate |
|---|---|---|
| **memclaw** | **62.71%** | 9/20 |
| mem0 | 55.96% | 11/20 |
| none | 53.64% | 7/20 |

| comparison | progress score | perm p | subtask McNemar |
|---|---|---|---|
| memclaw vs none | +9.07pp | 0.206 | **0.024** ✅ |
| memclaw vs mem0 | +6.75pp | 0.276 | **0.015** ✅ |
| mem0 vs none | +2.32pp | 0.499 | **1.0** ❌ |

**This was the point of the arm.** Had mem0 climbed to ~53% alongside `none`,
it would have meant the tier simply washes out memory differences and memclaw's
compressed margin was about the model rather than about memclaw. It did not:
**mem0 vs no-memory is a clean null — subtask correctness 8 vs 8, McNemar
p=1.0, an exact coin flip** — while memclaw separates from mem0 significantly
on the same metric (19 vs 6 own-only, p=0.015).

Correct reading of this tier: a stronger agent closes some of the gap to *no
memory*, but **memclaw still beats the competing memory system, and mem0 still
adds nothing measurable over having none at all.**

This also **restores the gpt-4.1 pattern and weakens the gemini "trend"**:
mem0-vs-none was a clean null at gpt-4.1 (p=0.94 math, p=0.45 phys), trended
positive-but-never-significant at gemini (p=0.076 math, p=0.170 phys), and is
flatly null again here. Three of four tiers say null; the gemini trend now
reads more like noise than a tier-dependent effect. Soften any claim that mem0
improves at stronger agent tiers.

**Wrinkle to report honestly:** mem0's paper passrate (11/20) is *higher* than
memclaw's (9/20) despite subtask correctness strongly favouring memclaw. That
is the known `is_paper_correct` resolution problem — it scores the final
subtask only. **Do not cite that row on its own.**

**Provider-routing caveat:** this arm ran through OpenRouter while memclaw and
none ran through Azure. Same models and same judge model, but a different
serving stack — minor, and it does not touch the judge-leniency issue (all
three arms share `gpt-5-mini`), but note it if this arm ever looks anomalous.

~~**Cite as:** *...the effect is markedly smaller than at gpt-4.1 or
gemini-3.6-flash, driven mainly by a much stronger no-memory baseline.*~~
**RETRACTED 2026-09-01** — the "much stronger no-memory baseline" was largely
the `gpt-5-mini` judge. Cite the re-judged phys numbers instead: **+12.37pp,
subtask p=0.043** (progress score p=0.091 at n=20).

## MemoryArena math: gpt-5.6-sol (2026-08-26) — confirms the tier's weak effect, and narrows why

> ⚠️ **SUPERSEDED for absolute numbers and significance** by "gpt-5.6-sol
> RE-JUDGED on the common ruler" above. On the shared `gpt-4o-mini` judge math
> reads memclaw 41.62% / none 34.60%, gap **+7.02pp, perm p=0.0054 —
> significant**, not the +4.16pp p=0.141 below. Kept for the run record, the
> two operational traps, and the caveats.

The test the phys gpt-5.6-sol section called for: 354 subtasks has the power to
resolve a ~+9pp effect that 20 papers cannot. Run on Azure, same three tier
deviations as phys (temp 1.0, `gpt-5-mini` judge, judge `max_tokens` 16384).
Both arms clean: 40/40 papers, **0/354 empty responses in both**, 0 failures.
Configs `math_{memclaw,none}_gpt56sol.json`, output `./results/json/math_gpt56sol`,
sequential. Resumed across several sessions; final arm finished 13:05.

**Two operational traps cost ~8 hours on this run, both worth avoiding on any
overnight run.** (1) The machine **slept** at 01:35 and did not wake until
08:54 — a 7h19m dead stop mid-paper; the process survived and resumed on its
own, so nothing was lost but time. Idle timeout, hibernate, *and* lid-close are
three separate settings: `powercfg /change standby-timeout-ac 0`,
`/change hibernate-timeout-ac 0`, and the `LIDACTION` GUID set to 0 (do
nothing). Note these are **AC-only** here — on battery it still sleeps. Also
note Git Bash mangles a leading `/change` into a Windows path, so these need
`MSYS_NO_PATHCONV=1` or a PowerShell prompt. (2) At 09:53 a transient network
wobble emptied three retries on one paper and the 2026-08-24 safeguard
**aborted the whole run** rather than writing a fake result — working exactly
as designed, but it exits and stays exited, so a long run needs a human to
notice. Data on disk was clean; only the process died.

| arm | paper passrate | avg progress score |
|---|---|---|
| memclaw | **0.300** (12/40) | **37.45%** |
| none    | **0.150** (6/40)  | **33.29%** |

| metric | result | test | p |
|---|---|---|---|
| progress score (paired, 40 papers) | +4.16pp, 95% CI **[-1.24, +9.38]** — crosses zero | perm (20k) | **0.141** (not significant) |
| subtask correctness (354 subtasks) | 40 own-only vs 21 | McNemar exact | **0.020** ✅ |
| paper passrate (40 papers) | 12/40 vs 6/40 (9 vs 3 discordant) | McNemar exact | 0.146 (not significant) |

Per-paper wins: memclaw 18, none 8, tied 14.

**Same shape as phys at this tier — only subtask correctness clears, and it is
again the metric with the most resolution** (354 observations vs 40). Two tiers'
worth of evidence now says that at gpt-5.6-sol the paper-level effect is real in
direction but not resolvable at MemoryArena's n.

### But it does NOT confirm the "headroom in reverse" story from phys

Math across all three tiers:

| tier | memclaw | none | gap | perm p |
|---|---|---|---|---|
| gpt-4.1 | 23.95% | 19.03% | +4.92pp | 0.024 |
| gemini-3.6-flash | 35.16% | 27.39% | +7.76pp | 0.0006 |
| **gpt-5.6-sol** | **37.45%** | **33.29%** | **+4.16pp** | **0.141** |

**The math gap barely compressed** (+4.92 → +4.16pp) while both arms rose
together (~+13pp each). Contrast phys, where `none` jumped +21pp against
memclaw's +10pp and the gap halved. So phys's "a strong agent recovers what
weaker agents needed memory for" reading **does not replicate on math**.

What actually changed on math between gpt-4.1 and gpt-5.6-sol is the
**p-value, not the effect size** — a near-identical gap went from p=0.024 to
p=0.141. The likely cause is variance, not capability: **agent temperature is
1.0 at this tier** (gpt-5.6-sol rejects 0.0), which widens the paired-diff
distribution and the CI. That is a measurement artifact of the tier, not a
finding about memory.

**Revised reading, replacing the phys section's speculation:** the effect does
not obviously erode with agent strength. It peaks at gemini-3.6-flash across
both domains, and the gpt-5.6-sol tier is harder to measure (temp 1.0, lenient
judge) rather than clearly weaker. Phys's compression may be a domain effect,
a small-n effect, or real — one domain still is not enough to call it.

### Caveats

- **The `gpt-5-mini` judge is ~6pp more lenient** than the `gpt-4o-mini` judge
  used at every other tier. Both arms share it, so +4.16pp stands within-tier,
  but **37.45% / 33.29% must not enter a cross-tier table without this caveat**
  — some of the apparent baseline rise is judge leniency.
- Temperature 1.0, as above — inflates variance relative to every earlier tier.
- No mem0 arm at this tier (scope decision, unchanged) — **but a config now
  exists**: `configs/formal_reasoning_configs/phys_mem0_gpt56sol.json` (written
  2026-08-26, verified flattened-identical to the memclaw arm except
  `memory_system_name`/`description`), and `run_gpt56sol_phys.sh`'s arm loop is
  now `memclaw none mem0` so it inherits the per-arm contamination gate.
  memclaw/none are already 20/20 and skip instantly, so only mem0 spends.
  mem0 pre-flighted live 2026-08-26 through the running memory server
  (`/memory/initialize` and `/memory/wrap_user_prompt` both 200) — the SEARCH
  quota that killed the gemini mem0 arms in August is genuinely clear. ~$10-15,
  Azure-billed. Open question it answers: at this tier `none` jumped to 53.64%
  on phys; if mem0 lands near it, the tier washes out memory differences
  generally, and if mem0 stays low, memclaw still separates from a competing
  memory system. The 2-arm table quietly invites the pessimistic reading.

### The judge-leniency confound is NOT symmetric — this is the open hole

The caveats above say "both arms share the judge, so the within-tier gap
stands". That defence is weaker than it looks. **A lenient judge converts wrong
answers into right ones, and the weaker arm has more wrong answers available to
convert** — so leniency lifts `none` more than it lifts memclaw, which
*compresses the gap*. That is precisely the pattern measured at this tier in
both domains (phys +24.14 → +9.07pp, math significance lost). So "strong agents
need memory less" and "we swapped in a softer judge" are currently
indistinguishable, and the confound sits directly on the headline claim.

**✅ FIXED — the re-judge ran 2026-08-27 and is scored; see "gpt-5.6-sol
RE-JUDGED on the common ruler" above for the numbers that supersede this
section. Method, for the record: re-judge the gpt-5.6-sol results with
`gpt-4o-mini`** so every tier shares one ruler. The judge scores stored
`(query, response, ground_truth)` triples, so no agent re-run is needed — the
expensive half is already on disk. Azure refuses new `gpt-4o-mini` deployments,
but OpenRouter still serves it, and judging is ~172 calls for phys / 708 for
math at $0.15/M in with one-token outputs — roughly **$0.20 for both domains**.
This was implemented as `scripts/rejudge.py` (all-rows, sidecar output to
`results/json/{math,phys}_gpt56sol_rejudged/`), keeping the gpt-5-mini verdicts
as evidence. **The compression finding did not survive it — do not cite it.**

~~**Cite as:** *...paper-level progress-score gaps are positive but not
significant (math +4.16pp p=0.14, phys +9.07pp p=0.20).*~~ **RETRACTED
2026-09-01** — on the common ruler math is **+7.02pp, p=0.0054 (significant)**
and phys is **+12.37pp**. See the re-judge section above for the wording to
use.

## gpt-5.6-sol tier: moved to Azure AI Foundry (2026-08-25)

The OpenRouter account is dry (-$0.18) and this tier was never run there, so
the `gpt-5.6-sol` arms were repointed at an **Azure AI Foundry** resource
(`https://jyolsna.services.ai.azure.com/openai/v1`) which already has a
`gpt-5.6-sol` deployment. Azure billing, OpenRouter untouched.

**No backend code was needed.** The stock `openai` SDK talks to Foundry's
`/openai/v1` endpoint with ordinary Bearer auth — the same call shape
`OpenAIBackend` already makes — so this is a config change only. Two things
differ from an OpenAI/OpenRouter endpoint: Azure routes by **deployment
name** (hence `gpt-5.6-sol`, not `openai/gpt-5.6-sol`), and the classic
`/openai/deployments` listing 404s on a Foundry project resource — use
`/openai/v1/models` to see the catalog and probe `/chat/completions` to find
what is actually deployed.

**Deployed on that resource: `gpt-5.6-sol` and `gpt-5-mini`. Nothing else.**

### Three deviations from every earlier tier — cite them together

1. **Agent temperature is 1.0, not 0.0.** `gpt-5.6-sol` rejects 0.0 outright
   ("Only the default (1) value is supported"). Not an Azure quirk; OpenRouter
   would refuse it too. Both arms use 1.0, so within-tier comparison is fair,
   but absolute scores carry more sampling variance than earlier tiers.
2. **Judge is `gpt-5-mini`, not `gpt-4o-mini`.** Azure refuses new deployments
   of `gpt-4o-mini` (`ServiceModelDeprecating`; it stays callable until
   2027-04-14 but cannot be newly deployed), so the judge used by every run
   since 2026-08-02 cannot be hosted here. **Measured agreement: 88.8%
   (71/80)** on stratified `phys_gpt41` pairs, via `scripts/judge_agreement.py`
   (new, in `MemoryArena`). The disagreement is lopsided — **7 wrong→right vs
   2 right→wrong**, so gpt-5-mini is roughly **+6pp more lenient**.
   **Consequence: memclaw-vs-none within this tier is valid (both arms share
   the judge); absolute scores must NOT be placed in the same table as the
   gpt-4.1 / gemini-3.6-flash tiers without this caveat.**
3. **Judge `max_tokens` raised 4096 → 16384**, because a reasoning judge that
   spends its budget on reasoning returns empty — see below.

### Judge-side empty-verdict hole, closed

`math_env.judge` did `"yes" in output` on the raw chat output. An empty
output silently scored the subtask **wrong** with nothing logged — the exact
agent-side failure that contaminated the Opus 5 runs, but on the judge, and
invisible to `check_result_contamination.py`, which only inspects agent
responses. Now raises `RuntimeError`, which `run_math.py` surfaces as a
visible paper failure. This only became a live risk once the judge was a
reasoning model; it was latent before.

### Rate limits

The Foundry deployment rate-limits hard: **8 concurrent judge calls produced
57-68% empty/429 verdicts**, while the same calls run serially succeed. Two
workers is safe. Keep runs at `MATH_SHARD_COUNT=1` (the run scripts already
do). Any agreement or contamination figure computed at high concurrency
against this endpoint is poisoned and should be recomputed — the first two
judge-agreement passes (86.5%, 84.2%) were discarded for exactly this reason.

### Run scripts

`run_gpt56sol_{phys,math}.sh` now export `OPENAI_API_KEY=$AZURE_OPENAI_API_KEY`
and **deliberately `unset OPENAI_BASE_URL`** — `_act_with_tools` builds its own
client from that variable and has 401'd on every run to date, silently falling
back to single-shot reasoning (see "KNOWN HARNESS ISSUE" below). Exporting it
would make the tool loop start working and render this tier incomparable with
every recorded result. The OpenRouter balance gate is replaced by a check that
`AZURE_OPENAI_API_KEY` is set; Azure has no equivalent pre-flight balance API,
so the per-arm contamination scan is the only safety net here.

**The env server must be restarted with the Azure key in its own environment**
before running — it builds the judge from `OPENAI_API_KEY` at import time
(setup gotcha #1 below), so a server started with the OpenRouter key will keep
using it.

## MemoryArena math: setup gotchas (2026-08-02)

Four traps, all of which silently waste time:

1. **The env server needs `OPENAI_API_KEY` in its own environment.** Unlike
   travel (agent-side LLM only), math builds an **LLM judge inside the env
   server** (`env/env_systems/math_env.py` → `create_backend`), which reads
   `os.getenv("OPENAI_API_KEY")` from the *server* process. Starting the env
   server without it makes every `/env/initialize` return 500. Launch it with
   `OPENAI_API_KEY=$OPENROUTER_API_KEY` exported.
2. **`run_math.py` used to swallow every per-paper exception** and then log
   `PAPER ... COMPLETED`, so a run where all 40 papers failed looked like a
   clean pass that just wrote no results — this is exactly how trap #1 first
   presented. Now fixed: failures are logged with traceback, collected, and
   reported as `N of M papers FAILED` at the end.
3. **`main(json_config)` is called twice** at the bottom of `run_math.py`
   (an unguarded call followed by a try/except-wrapped one — upstream sloppiness,
   left as-is). Harmless because of the per-paper resume-skip, but it re-loads
   the dataset and re-walks all papers, so expect a duplicate log banner.
4. **`auto_eval_after_run` does nothing** — the `eval_and_print_result(...)`
   call inside `run_math.py` is commented out. Score manually:
   `python -m env.env_systems.formal_reasoning_env.eval <config>`.
   Eval treats each *subdirectory* of `json_output_dir` as a "method", and
   `_get_json_output_dir` already appends the memory-system name — so both
   configs point at `./results/json/math` and one eval call prints memclaw and
   none side by side.

Harness additions (in `MemoryArena`, uncommitted):

- `NullMemoryClient` + `_build_memory_client` in `run_math.py`: math had **no
  no-memory path** (`MemoryClient.__init__` POSTs `/memory/initialize`, which
  400s for `"none"`). The null client passes prompts through unwrapped and
  drops writes — the math equivalent of travel's `memory_system=None`.
- `MATH_SHARD_COUNT` / `MATH_SHARD_INDEX` paper-level sharding, same scheme as
  travel; `run_math_shards.ps1` launches shards (sets `PYTHONIOENCODING=utf-8`,
  maps the OpenRouter key, skips the memory-server check for the `none` arm).
- `configs/formal_reasoning_configs/math_none.json` (new): byte-identical to
  `math_memclaw.json` except `memory_system_name` — verified by diffing the
  flattened configs, so any gap is attributable to memory alone.

## Next action

**MemoryArena-Rotation's formal-reasoning track is done at gpt-4.1** (as of
2026-08-09): travel is **closed** (true null, gpt-4o-mini); math and phys are
both **closed at gpt-4.1 across all three arms** — memclaw > mem0 ≈ none in
both domains, with phys's memclaw-vs-none effect ~4x math's. Further
gpt-4o-mini results (2026-08-02) are superseded as headline numbers but kept
as the lower-model-tier comparison point.

**A second agent-model tier was added 2026-08-12** (`google/gemini-3.6-flash`)
to test whether the effect is gpt-4.1-specific. It is not: phys replicated
with a *larger* effect (+24.14pp, subtask McNemar p=4.2e-07), and **math now
replicates too as of 2026-08-19** (+7.76pp, subtask McNemar p=0.0007) after
resuming from the 2026-08-18 contamination — see "MemoryArena math:
gemini-3.6-flash — complete" above. **Both domains are now closed at the
gemini-3.6-flash tier for the memclaw-vs-none comparison.**

**mem0 at gemini tier is now fully run in both domains (as of 2026-08-20),
and the story is consistent but still short of significant.** Both math
(+3.74pp progress score, p=0.076) and phys (+9.25pp, p=0.170) show mem0
trending *above* no-memory at the gemini tier — a different shape than
gpt-4.1, where mem0≈none was a clean null in both domains (p=0.94, p=0.45).
Neither gemini result individually clears significance, but the direction
agreeing across two domains is worth carrying forward as "trending, not
proven" rather than dismissing as noise. memclaw still beats mem0 in both
domains regardless (math subtask p=0.040, phys progress score p=0.035 and
subtask p=0.0005) — the core memclaw-vs-mem0 finding is unaffected. **The
mem0 SEARCH-quota key issue that originally blocked both gemini mem0 arms is
resolved** — the account was moved to a key/plan with working search
(verified live 2026-08-19). See "MemoryArena math: gemini-3.6-flash —
complete" and "MemoryArena phys: gpt-4.1 replication" (mem0 addendum) above
for full numbers.

**The gemini-3.6-flash tier is now fully closed — all three arms, both
domains, done as of 2026-08-20.** Nothing left to run at this tier.

Two further agent models were scoped but **not run** on cost grounds
(2026-08-12): `anthropic/claude-opus-5` and `openai/gpt-5.6-sol`, both verified
available through OpenRouter with the harness's exact call shape. Estimated
~$125-145 each for a full 2-domain × 3-arm sweep (~$250-290 combined),
versus ~$38 for gemini, which is why gemini went first.

**Both were attempted on this machine 2026-08-23/24 and neither produced a
citable result here — see "MemoryArena opus5 / gpt-5.6-sol: attempted, no
usable result yet" below.** No scores are recorded for either tier from this
checkout, deliberately: the only paired-clean data that survives locally is 5
phys papers, and this file's own method note rejects an aggregate at that n
as evidence.

The earlier external report that **Opus 5 math had reached 28/40 papers on a
separate machine** is a separate run from the local attempts above and may
well be intact — `results/json/math_opus5/` here holds only a quarantined 402
batch, which says nothing about what happened elsewhere. Two things to do
before citing it, in this order:

1. **Pull the per-paper logs over** (Next action item 4) — a paper count
   reported second-hand is not a score.
2. **Run `check_result_contamination.py` on it before anything else.** Any
   Opus 5 run predating the 2026-08-24 fixes used `max_tokens: 8192` on the
   unpatched `llm_backend.py`, which is exactly the combination that produced
   18-33% silently-empty subtasks locally. A clean-looking "28/40 completed"
   is the *expected* appearance of that bug, not evidence against it.

Next, in priority order:

0b. ✅ **DONE 2026-09-13 for phys — see "TOOL-LOOP ROBUSTNESS RUN: COMPLETE"
   above for the result (+12.75pp, subtask p=0.0118; the gap halves vs the
   broken path). Remaining: the math tool-loop pair (memclaw 5/40, none 0/40,
   ~$6-8), which is the only sample large enough to resolve the halving.**
   Historical detail below.

   **STATUS UPDATE 2026-09-10 — item 0 is ~80% DONE, not unstarted.** Read
   this before planning it. On disk in `MemoryArena`:
   - **The one-line fix is already implemented and committed**, deliberately
     opt-in: `agent/math.py:443-455` uses the agent's configured `base_url`
     only when `MATH_ENABLE_TOOL_LOOP=1`, so default behaviour stays
     byte-identical to every prior run and old results remain comparable.
   - **Config pair exists and is valid**: `phys_{memclaw,none}_gemini36_toolloop.json`,
     verified flattened-identical apart from `memory_system_name`/`description`,
     output `./results/json/phys_gemini36_toolloop`. Note the tier chosen is
     **gemini-3.6-flash, not gpt-4.1** as the plan below assumed — which is
     the better call, since `phys_gemini36` is the strongest existing pair
     (+24.14pp) and therefore the sternest test of whether the effect survives
     a working agent loop.
   - **The tool loop actually runs.** **0 `tool loop failed` across all 144
     stored subtasks**, against 708/708 failing in every result recorded
     before this. That alone answers the objection this item exists for.
   - **Remaining work: 7 papers of the `none` arm** — `0000.0000`,
     `0000.0003`, `1304.1806`, `2004.01171`, `2010.06947`, `2310.20045`,
     `2401.09908`. memclaw is 20/20. Runs resume per paper, so this is a
     single command and roughly **$1** at gemini-3.6-flash rates.
   - **One contamination spot**: `memclaw/0000.0003` has 1 empty response of 3
     subtasks (1/86 for the arm). `none` is clean at 0/58. Re-run that paper
     or record it, but do not score without noting it.
   - A `_empty_backup_20260909/` quarantine folder holds 1 paper — evidence
     from an earlier pass, excluded from scoring, do not merge back.

0. **TOOL-LOOP ROBUSTNESS RUN — do this before publishing anything externally
   (added 2026-09-02).** Every MemoryArena number in this file was produced by
   a single-shot reasoner, because `_act_with_tools` 401s and silently falls
   back (see "KNOWN HARNESS ISSUE" above). That is disclosed in the README and
   the paired comparisons are unaffected — but it is the single most damaging
   objection an outside reader can raise: *the agent loop was broken for the
   entire study*. Converting it from a caveat into a measured robustness check
   is cheap:
   - Fix is one line — pass the config's `base_url` into the client in
     `_act_with_tools`, or export `OPENAI_BASE_URL` in the run scripts.
   - Re-run **phys gpt-4.1 only**, 2 arms × 20 papers, at the cheapest tier
     already characterised. Estimated **$3-5**.
   - Write it up as a separate tier (`phys_gpt41_toolloop`), NOT merged into
     the existing numbers — the whole point is that the agent code path
     differs, so it is a new comparison, not a correction to the old one.
   - If the effect survives, one paragraph kills the biggest objection. If it
     does not survive, that is something to know before publishing, not after.

1. ~~**LoCoMo / LongMemEval**~~ — **DROPPED 2026-08-25.** Decided not to run
   these. The scaffolding (`suites/recall_accuracy_locomo`,
   `suites/recall_accuracy_longmemeval`) and the dataset READMEs are left in
   place but stay unpopulated; `scripts/fetch_locomo.py` was never written and
   now won't be. Two consequences worth recording, since they were the reasons
   this used to be priority 1:
   - The product repo's LoCoMo/LongMemEval numbers (77.6% / 72.5% accuracy,
     2026-04-19) remain **uncontrolled** — no baseline arm, no n, no judge
     model, no statistical test. This project will not produce the paired,
     comparative version, so those figures should keep being described as
     unbaselined whenever they are cited.
   - **The token-efficiency contradiction stays unresolved.** `BENCHMARKS.md`
     claims 96.6% / 98.2% token savings vs full context; our travel
     measurement found memclaw used *more* than the full-context-style
     control (112k vs 104k input tokens/group, ~1.07x). The `full_context`
     condition in `runners/recall_accuracy.py` was the comparator that would
     have settled it. Do not circulate the two numbers side by side as if
     they agree.

2. **Shopping stays deferred but is now more worth doing** — two formal-reasoning
   domains discriminating at gpt-4.1 makes a third (different-shaped) task
   worthwhile, but it needs a multi-GB product DB, a JDK, spacy
   `en_core_web_lg`, and an extra upstream service (see table) — still a
   heavy, deliberate setup, not a quick add.
3. Investigate the abandoned `math_gpt5mini` partial run (`results/json/math_gpt5mini/`,
   2 papers done, memclaw only) found 2026-08-04 — figure out whether it's
   worth resuming/discarding, and who/what started it.
4. **Pull over every result that exists only on another machine.** This has
   quietly become a recurring gap, so it is now one tracked list rather than
   scattered notes. In each case the run may be perfectly good — the problem
   is that from this checkout it can only be *quoted*, never re-scored,
   contamination-scanned, or re-analysed, and the 2026-08-18/24 incidents
   both showed that a result nobody can scan is a result nobody should cite.
   **⚠️ 2026-09-14: THE OTHER MACHINE IS GONE. Nothing on this list can ever be
   pulled over.** Resolutions, so this item can finally be closed:
   - **`math_gpt41/mem0` — ✅ RECOVERED**, and never actually on that machine: it
     was in `~/Downloads/memoryarena-evidence-2026-08-05/`. 40 papers, 354
     subtasks, 0/354 empty. Now in `repro/results/math_gpt41/mem0/`, which makes
     Caura-vs-mem0 poolable at gpt-4.1 for the first time (+6.14pp, cluster
     p=0.00715). **Look in Downloads before declaring a result stranded.**
   - **STATE-Bench `outputs/` — ❌ gone, and no longer needed.** See the #36
     section above: the version question is answered by arithmetic instead.
   - **Opus 5 math "28/40" — ❌ gone, and worth nothing anyway.** It predated the
     2026-08-24 fixes, so it ran `max_tokens: 8192` on the unpatched
     `llm_backend.py` — the exact combination that silently emptied 18-33% of
     subtasks locally. A clean-looking paper count is the *expected* appearance
     of that bug. Do not mourn it; `math_opus5` would need a fresh run (~$148).
   - **CL-Bench quick_test** — was never a result (3 runs × 5 hands, pure
     variance). Nothing lost.
   - **`math_gpt41/mem0` per-paper logs** — arm ran on the second machine
     2026-08-04; summary figures were reconciled into this file but the logs
     never arrived, so the mem0 section's numbers cannot be re-derived here.
   - **Opus 5 math "28/40 papers"** — external report, separate machine.
     **Scan it for empty responses the moment it lands**: any Opus 5 run
     predating the 2026-08-24 fixes hit `max_tokens: 8192` on the unpatched
     `llm_backend.py`, the exact combination that silently emptied 18-33% of
     subtasks locally while reporting a clean paper count.
   Standing rule for anything pulled in: `check_result_contamination.py`
   first, `paired_stats.py` second, record third.
5. Optional, only for an external-facing writeup: compute a pooled math+phys
   estimate with a domain fixed-effect (not a naive average — see caveat in
   the phys section above).

Method note carried forward from travel: **always run a paired control at the
same scale, and test the difference** (paired bootstrap CI + permutation test
over per-item scores) before treating any gap as real. A raw aggregate delta
at small n is not evidence.

## MemoryArena mem0 arm: setup done, run blocked on this machine's RAM (2026-08-04)

**Update:** the math run described below as blocked was completed the same
day on a different machine — see "MemoryArena math: mem0 arm result
(2026-08-04)" above for the actual numbers. **Phys then ran on this machine
2026-08-05 at `-Shards 1`** and completed fine — see "MemoryArena phys: mem0
arm result" above. So the `-Shards 1` fallback suggested below does work on
7.34GB; the OOM was specifically 4 parallel shards. Both mem0 arms are now
done. The RAM-exhaustion story below is kept as-is for the setup/gotcha
record.

`MEM0_API_KEY` is now in `MemoryArena/.env` (mem0ai SDK was already installed,
v2.0.14). **Gotcha:** the first paste of the key had a hidden zero-width
space (U+200B) inside it, right after `m0-` — silently breaks auth, no error
until you actually call the API. Verified clean with a raw-bytes read after
stripping it; confirmed working via direct SDK `add`/`search` calls and via
the memory server's `/memory/initialize`+`/memory/add`+`/memory/wrap_user_prompt`
for `memory_system_name: "mem0"`.

**Had to restart the memory server** (port 8000) after adding the key —
`memory/server.py` / `memory/memory_systems/mem0.py` both call
`load_dotenv()` once at import, so a server process already running from
before the key was added never picks it up. If resuming on a machine where
the memory server is already up, restart it first.

**Noted but not a blocker:** mem0's `add` is asynchronous — memories weren't
searchable even ~30s after an `add` call in manual testing. This is inherent
to mem0's ingestion pipeline (fact extraction runs server-side, async), not
a bug here. Worth watching in the results: if subtask-to-subtask timing in
the actual run is faster than mem0's ingestion latency, mem0's arm could
look artificially weak for reasons unrelated to memory quality. Not worth
engineering around — this is realistic mem0 behavior any real user would
hit too, so let the run capture it honestly.

New configs, both gpt-4.1 tier to match the significant memclaw/none results,
both verified flattened-identical to their memclaw counterparts except
`memory_system_name`/`description` (same method as `math_none.json`):
- `configs/formal_reasoning_configs/math_mem0_gpt41.json` — output dir
  `./results/json/math_gpt41` (joins existing memclaw/none there, so one
  eval call will compare all three arms).
- `configs/formal_reasoning_configs/phys_mem0_gpt41.json` — output dir
  `./results/json/phys_gpt41`, same reasoning.
- (Pre-existing `math_mem0.json` in the repo is stale — gpt-5-mini,
  placeholder `<OPENAI_BASE_URL>`, points at the old `results/json/math`
  gpt-4o-mini dir. Not used for this; left as-is.)

**Math run attempt (2026-08-04) failed clean, no papers processed:**
`run_math_shards.ps1 -Config math_mem0_gpt41.json -Shards 4` — all 4 shards
died within ~1 min of launch with `OpenBLAS error: Memory allocation still
failed after 10 retries, giving up.` This machine has only **7.34GB total
RAM** and was down to **~0.82GB free** at launch (many Chrome/VS
Code/Claude processes already running) — not a mem0 or config problem, pure
host memory exhaustion from 4 parallel shards. Confirmed no
`results/json/math_gpt41/mem0/` directory was even created, so this is a
clean restart, not a resume — no partial results to reconcile.

**Decision: retry on a different (more capable) machine** rather than
fighting this one down to 1 shard. Everything needed travels with the repo:
`.env` has the key, both configs exist and are verified correct, memory
server code needs no changes. On the new machine: start `env/env_server.py`
+ `memory/server.py` (see setup_formal_reasoning.md), then
`.\run_math_shards.ps1 -Config configs/formal_reasoning_configs/math_mem0_gpt41.json -Shards 4`
followed by the phys equivalent. If RAM is still tight, fall back to
`-Shards 1` (sequential, ~1.5-2hrs for math's 40 papers vs ~27min at 4
shards) rather than risking another OOM mid-run.

Once both arms complete, score with:
`python -m env.env_systems.formal_reasoning_env.eval configs/formal_reasoning_configs/math_mem0_gpt41.json`
(and the phys equivalent) — same eval call format used for memclaw/none,
now with three method subdirectories to compare instead of two.

STATE-Bench is no longer blocked on *acquiring* Azure — the resource exists and
`gpt-5.4` is in its catalog, just undeployed (verified 2026-08-26, see table above).
Deploy it, fill the still-template `.env`, then run the Agent Learning Track only.

## STATE-Bench: ran on v0.7.x — scorer bug #36 applies, RE-SCORE not re-run (2026-09-07)

**Confirmed: the scored run used v0.7.x.** That version carries upstream issue
**#36** — `scoring.py::_record_identity` keyed child records by their parent id
(it checked `order_id`/`customer_id`/`cart_id` before the record's own
`item_id`), collapsing sibling `order_items` and producing **false
`task_completion = 0`**. Fixed in 0.8.x: `_record_identity` now prefers
`ENTITY_PRIMARY_KEY[entity_type]` before falling back to the old field-priority
heuristic (verified in the 0.8.1 checkout, `state_bench/scoring.py:301-319`).

**The results are not safe to cite as they stand.** The bug produces false
failures, so scores are depressed. It is a *scoring* bug, not an agent or
simulator bug, and it is not arm-specific by design — but the two arms produce
different trajectories, so it can fire at different rates per arm and bias the
comparison. `shopping_assistant` (Caura 53% vs baseline 55%, the only negative
domain) is the most exposed, since `order_items`/`orders`/`cart_id` are its
entities.

**Do NOT re-run the benchmark.** `state_bench/scripts/score.py` exists exactly
for this: *"Score existing trajectories with the current metric judges. Reads
trajectory JSONs... and updates the same trajectory files in place by default.
**Does not re-run agents.**"* The agent turns and the multi-turn user simulator
— the expensive half — are already on disk.

    # on the run machine, from a 0.8.1 checkout, pointed at the v0.7.x outputs
    cp -r outputs outputs_v07x_backup          # keep the original verdicts
    uv run python -m state_bench.scripts.score         --domain shopping_assistant --num-runs 5 --results-dir outputs/shopping_assistant_memclaw
    # repeat per domain and arm, then recompute metrics
    uv run python -m state_bench.scripts.compute_metrics --results-dir outputs/shopping_assistant_memclaw

**Cost:** judge calls only, roughly 2 per trajectory (completion + UX) against
the locked GPT-5.4, so on the order of 3000 calls for all six domain-arms.
`--no-ux-score` halves that if only `task_completion` needs correcting.

**✅ IT IS FREE — verified 2026-09-08 against the local 0.8.1 checkout. Do not
pay for the judge re-run above.** The #36 bug lives entirely in the
*deterministic* half, and the two halves are stored separately:
`score.py:161-171` writes `state_requirements_met` (deterministic) and
`task_requirements_met` (LLM judge) as distinct fields, `combine_task_completion`
(`scoring.py:31-38`) is just `state AND task`, `state_diff` is persisted on every
trajectory (`score.py:146`), and `evaluate_state_requirements(task, state_diff)`
takes no client. So the state half can be recomputed under 0.8.x and recombined
with the **stored** judge verdict at zero cost and zero LLM calls. UX scores are
untouched by #36.

Tool: **`scripts/rescore_state_only.py`** (this repo, written 2026-09-08).
Imports `state_bench`, so run it from a 0.8.x checkout with that checkout's
interpreter:

    cp -r outputs outputs_v07x_backup          # rewrites in place
    ./.venv/Scripts/python.exe <path>/scripts/rescore_state_only.py         --domain shopping_assistant --results-dir outputs/shopping_assistant_memclaw --num-runs 5
    # then, per domain-arm:
    uv run python -m state_bench.scripts.compute_metrics --results-dir outputs/shopping_assistant_memclaw

`--dry-run` reports how many `task_completion_pass` bits flip without writing —
**run that first per domain-arm and record the flip counts**, since that is the
measured blast radius of #36 on our results. `--self-check` runs an offline
assertion (real task file, empty `state_diff`: state must fail and must veto a
passing stored judge verdict; an unjudged trajectory must stay `None`) — passes
as of 2026-09-08.

**⛔ THE RE-SCORE IS NOW PERMANENTLY IMPOSSIBLE — and no longer needed
(2026-09-14).** The machine holding `outputs/` is gone for good, so the free
re-score above can never run and the lockfile can never be read. Both routes to
the version question are closed.

**Resolved by a different route instead: v0.7.0 is ruled out by arithmetic.**
#36 is *deterministic*, so the tasks it breaks are computable from the shipped
task definitions with no trajectories at all. Counting them gives a hard
ceiling on pass@1 per domain:

| domain | #36 breaks | v0.7.0 ceiling | our pass@1 |
|---|---|---|---|
| travel | 2/50 | 96% | 70% / 61% |
| **customer_support** | **42/50** | **16%** | **71% / 59%** |
| shopping_assistant | 0/50 | 100% | 53% / 55% |

`customer_support` could not have exceeded **16%** under v0.7.0. We measured
**71%**. The run was not scored by v0.7.0, so our numbers are not depressed by
#36. Tool: **`scripts/state36_blast_radius.py`** (self-checking); full argument
and its limits in **`repro/STATE_BENCH_ISSUE36.md`**.

**Two corrections this forces to the notes above.** (1) The claim that
`shopping_assistant` is "the most exposed" is **backwards** — `order_items` and
`orders` are *customer_support* entities, and shopping has **zero** exposure, so
our one negative domain is a real measurement. (2) What is established is "not
v0.7.0", never "v0.8.1" — the exact minor version is unknowable now.

`scripts/rescore_state_only.py` is kept: it is correct and self-checked, and
would work immediately if trajectories ever resurface. It is simply unrunnable.

**Standing rule this reinforces:** record the harness version and commit in the
run output. Nothing in our outputs states which version produced them, which is
why this took an external reviewer to surface.

## STATE-Bench: Agent Learning Track — first full run (2026-08-26)

**Ran on the other machine, not this one.** Offline learning-build (300 memclaw
writes across 3 domains × 100 train trajectories) then the full official
evaluation: 3 domains × 2 arms × 5 runs × 50 held-out test tasks =
**1500 scored trajectories, 0 errors**. Locked eval client (simulator + judge)
is `gpt-5.4` on a real Azure AI Foundry resource; agent-under-test is
`gpt-5.6-sol` — the newest model actually *deployed* there. (The catalog lists
`claude-opus-5`, `claude-sonnet-5` etc. too, but every Claude tier 404s as
`DeploymentNotFound` — cataloged, not provisioned. Independently confirmed from
this machine 2026-08-26.)

| Domain | Arm | pass@1 | pass^5 | Mean UX (/5) |
|---|---|---|---|---|
| travel | memclaw | **70% ± 3%** | **58%** | **3.98** |
| travel | baseline (no memory) | 61% ± 7% | 34% | 3.72 |
| travel | **Δ** | **+9pp** | **+24pp** | **+0.26** |
| customer_support | memclaw | **71% ± 4%** | **58%** | **4.10** |
| customer_support | baseline (no memory) | 59% ± 3% | 40% | 3.53 |
| customer_support | **Δ** | **+12pp** | **+18pp** | **+0.57** |
| shopping_assistant | memclaw | 53% ± 4% | 42% | 3.92 |
| shopping_assistant | baseline (no memory) | 55% ± 2% | 48% | 3.83 |
| shopping_assistant | **Δ** | −2pp | −6pp | +0.09 |

**Honest read**: a clear, consistent win on `travel` and `customer_support`
across all three metrics, and a wash-to-slightly-behind result on
`shopping_assistant` (pass@1 CIs overlap; pass^5 favours the baseline by a real
6pp; UX edge to memclaw is small). **Not a clean sweep — 2 of 3 domains,
reported as it landed rather than cherry-picked.**

**This is the largest memclaw result in the project** — 1500 trajectories with
0 errors against MemoryArena's 354-subtask ceiling, on a genuinely different
task shape (multi-turn agentic dialogue vs formal reasoning). It is also the
only benchmark here whose no-memory control is part of the official protocol
rather than constructed by us.

> ⚠️ **THAT LAST CLAIM IS FALSE — corrected 2026-09-07 after external review
> caught it.** `docs/AGENT_LEARNING_TRACK.md` defines the `retrieve_learnings`
> hook but **no baseline arm**, and the string "baseline" appears nowhere in
> STATE-Bench's source or docs (only inside third-party packages in `.venv`).
> `orchestrator.py:171` is `resolved_agent_class = agent_class or
> StateBenchAgent`, i.e. the stock agent is just the default. Our no-memory
> control is **constructed by us**, exactly like the MemoryArena ones. It is
> still a sound control (`MemclawAgent` subclasses `StateBenchAgent` and
> overrides only `retrieve_learnings`, so the arms share model, loop and
> prompt) but it carries no special protocol standing. Do not describe it as
> official.

### Six real bugs found and fixed

1. **venv cross-machine path** — `.venv/pyvenv.cfg`'s `home` pointed at a dead
   Windows profile from wherever it was built. Repointed; packages were intact.
2. **`result.isError` → `result.is_error`** in `agents/memclaw_agent.py`
   (pydantic field rename in the `mcp` SDK, same family as the
   `streamablehttp_client` → `streamable_http_client` rename) — crashed every
   memclaw tool call with `AttributeError`.
3. **`build_learnings` had no length cap and no per-item error handling.**
   MemClaw's server enforces a 10,000-char content limit; one long trajectory
   summary exceeded it and, with no try/except in the write loop, killed the
   entire 300-write batch with zero receipts. Fixed: truncate to fit, catch and
   record per-task failures. Rerun clean, 300/300, ~11 min.
4. **CRLF/LF prompt-hash mismatch, all 12 locked prompt files.** `run_batch`
   refused to start — the Windows checkout's blobs are CRLF but the locked
   hashes were computed against LF (confirmed: stripping the CR bytes
   reproduces the expected hash exactly). Upstream inconsistency, not something
   to fix by editing prompt text — normalized line endings in place, byte-only.
5. **`MemclawAgent.__init__(self, *args, **kwargs)` silently dropped
   `--agent-model-reasoning-level`.** `orchestrator.py` decides whether to
   forward `agent_reasoning_effort` by *introspecting the signature*, which a
   `*args/**kwargs` form defeats — so the flag vanished behind a
   `logger.warning` and `gpt-5.6-sol` got called with `temperature`, which 400s.
   Fixed by declaring the real parameter list.
6. **Systemic Windows locale-encoding crash — 14 call sites.** Every
   `open(path, "w")` / `Path.write_text()` (and the read-backs too) defaulted to
   cp1252 and crashed on the first non-cp1252 character — first hit on a travel
   route containing an arrow glyph (U+2192), *after* a full paid
   agent+simulator+judge turn had already run. Same bug family as MemoryArena's
   travel cp1252 crash. All 14 sites now pass `encoding="utf-8"`.

(A seventh looked like a bug and is not: `compute_metrics --split all` refuses
to score an incomplete run, listing every missing task. That is a working
safety guard.)

### Concurrency

All 6 domain-arm jobs share one `gpt-5.6-sol` Azure deployment. 6 jobs at
`--num-workers 10` produced constant `429`s in `eastus` — though tenacity's
backoff meant no task actually *failed*, just heavy retry overhead. Settled on
**6 concurrent jobs at `--num-workers 3` each (18 total)**: clean, zero
rate-limit hits, ~16 task-completions/min. **`run_batch` has no resume/skip
logic** — `work_items` is built unconditionally from every
`(run_idx, task_file)` pair regardless of what is on disk — so a
kill-and-relaunch redoes everything. Plan for that.

One unexplained interruption: all 6 jobs were killed externally at ~389/1500,
cause unknown, not reproduced after relaunch. Lost ~15 min.

### Caveats

- **`Mean cost/task` is unmeasured — `$0.0000` for every arm.** STATE-Bench's
  cost reporting is opt-in via `self.add_cost_usd(...)`, which neither
  `MemclawAgent` nor the baseline calls. **No dollar or token comparison exists
  for this benchmark**, which matters because token efficiency is exactly the
  claim LoCoMo/LongMemEval were meant to settle and now never will.
- **Single agent-model tier** (`gpt-5.6-sol`). Unlike MemoryArena's multi-tier
  sweep, nothing checks whether the shopping_assistant softness or the two wins
  are model-specific. Given MemoryArena found effect size varies a lot by tier,
  treat one tier as one data point.
- Per-task breakdowns and `metrics.json` for all 6 arms live under
  `outputs/<domain>_<arm>/` in that checkout — **not present here**; pull them
  over before anything is re-scored or re-analysed (standing rule, see
  "Next action").

## CL-Bench: state as of 2026-08-26 — quick_test only, real run still blocked

**quick_test ran 2026-08-19** on the other machine (`clbench run
exploitable_poker --system memclaw --schedule quick_test`, model
`openrouter/openai/gpt-4o`), the first time the integration ever executed
end-to-end since being wired in on 2026-07-29:

| | value |
|---|---|
| Final cumulative gain | -5.5000 |
| Final cumulative reward | -1.0000 |
| Baseline reward total | +4.5000 |
| Run rewards | Run 1: +0.5, Run 2: -5.0, Run 3: +1.5 |

**Do not read this as a result in either direction.** `quick_test` is 3 runs ×
5 hands — poker variance at that n swamps any signal, and the negative gain is
noise, not evidence memclaw hurts. Its only job was proving the wiring works.

**The real comparison (full `default` schedule, 120 instances × 5 runs) is
blocked, and has now failed on two *different* mechanisms:**

- **2026-08-19:** OpenRouter `402` — *"requires more credits, or fewer
  max_tokens... you requested up to 16384 tokens, but can only afford N"*. Not
  an empty account (`limit_remaining: 120.93` at the time). The affordable
  ceiling *dropped* between attempts (3160 → 1848) independent of worker count.
- **2026-08-26:** two attempts at `openai/gpt-5.4` (matching the tier of the
  existing baselines `mem0-gpt-5.4`, `ace-gpt-5.4`, `icl-gpt-5.4`), both
  reaching run 4-5 of 5 before failing on
  `in_flight_budget_exhausted / openrouter_in_flight_budget` — a credit
  *reservation* ceiling on not-yet-settled requests. Retried sequentially at
  `--max-workers 6` and it failed **earlier** (run 2 of 5), so lowering
  concurrency is not the fix. ~$14 burned across both, $46.71 of $200 left.

**Likely cause**: `gpt-5.4` at high reasoning effort reserves a large
`max_tokens`-sized budget chunk per in-flight request, so a handful of
concurrent calls exceed the ceiling regardless of actual balance.

**`clbench run` has no resume** — a third attempt redoes the whole schedule.
Per the standing "don't retry blindly" rule, two informed attempts is enough
for one session. ~~**Untried levers, in order:**~~ **The likely real fix was implemented
2026-09-02 (`cf29fc2`) and is untested only because there is no budget.**
`litellm.completion` was called with **no `max_tokens`**, so OpenRouter reserved
the model's full `max_output_tokens` (16384 for gpt-5.4) per in-flight request;
at the schedule's 12 workers that reservation exceeds the ceiling regardless of
actual balance — which explains why dropping 24 → 6 workers made it fail
*earlier*, not later. `CLBENCH_MAX_OUTPUT_TOKENS` caps it
(`src/systems/utils/structured_output.py`); unset leaves upstream behaviour
untouched so no existing result changes, and a response that actually hits the
cap logs a `finish_reason=length` warning so truncation cannot pass silently.
Remaining untried lever if it still trips: `--max-workers 1` (the attempts went
24 → 6, never to 1).

### ✅ in_flight_budget_exhausted SOLVED — canary run 2026-09-09

`CLBENCH_MAX_OUTPUT_TOKENS` (cf29fc2) is **verified working at the exact
concurrency that failed three times**. Canary: `--task-params
'{"schedule":"quick_test"}' --runs 12 --max-workers 12` at
`openrouter/openai/gpt-5.4` with `CLBENCH_MAX_OUTPUT_TOKENS=2048` —
**12/12 runs completed, 65 instances, zero in-flight errors, zero
`finish_reason=length` truncations.** Run group
`canary-gpt54-inflight`.

The diagnosis was right. A direct probe first showed `gpt-5.4` returns a
complete structured poker action in **26-29 output tokens** at
`finish_reason=stop`, so the unset `max_tokens` was making OpenRouter reserve
16384 tokens per in-flight request to carry ~29 tokens of answer. Capping at
2048 is an 8x cut in the reservation and loses nothing. This also explains the
old tell nobody could place: dropping 24 -> 6 workers made it fail *earlier*,
because the reservation is per-request, not per-worker-pool.

~~**Measured cost at gpt-5.4: $0.01422/instance**~~ — **INVALID, corrected
same day. That canary ran with a dead `MEMCLAW_API_KEY` and measured a
no-memory arm wearing a memclaw label.** 496 `401`s against
`https://memclaw.net/mcp`, each swallowed by `src/systems/memclaw/system.py`
as `memclaw recall failed, continuing without memories`. The run completed,
reported real per-hand rewards and exited 0. $0.01422/instance is therefore a
**floor** — no memory context ever entered a prompt — and the ~$8.90 default
projection built on it is too low by however much `top_k: 10` recalled
memories add per call. See the credential note below; re-measured in run group
`canary2-realkey`.

**This is the third instance in this project of the same failure class** (after
the 2026-08-13 exhausted-balance empties and the 2026-08-24 reasoning-token
empties): an API failure swallowed into a clean-looking completed result that
no exit code, log summary or paper/run count distinguishes from a good one.
Here it is CL-Bench's own `except` around recall, not our harness. **Standing
rule extended: for any memory-system arm, grep the run log for auth/recall
failures before trusting a single number from it** — "completed" means every
instance wrote *a* result, never that memory was actually in the loop.

**No control arm needs running at this tier.** `final_results/runs/` ships five
gpt-5.4 systems on `exploitable_poker` at the same `default` schedule —
`icl-gpt-5.4`, `mem0-gpt-5.4`, `ace-gpt-5.4`, `icl-notepad-gpt-5.4`,
`codex-gpt-5.4`. That is the competitor set for a real multi-system chart, but
it is **upstream's data, not ours**: different machine, date and harness
version, so it is a leaderboard comparison, NOT a paired one. Say so explicitly
wherever it is cited. The only paired control we own is the gpt-4o `icl`
default group from 2026-07-28.

**Fourth default attempt 2026-09-10: reached ~94%, then DEADLOCKED in
upstream's process pool. $27.19 spent, zero output, unrecoverable.** This one
is worth reading before any further CL-Bench spend, because credits were NOT
the problem: **auto top-up fired correctly** (`total_credits` 1590 -> 1615 at a
balance of ~$4.8, so its threshold is simply low, which is why it had not
triggered at $22/$12/$5.30 earlier) and there were **zero 402s all run**.

Diagnosed live with `py-spy dump` on every process:

| process | stack |
|---|---|
| parent main thread | `as_completed` (`_base.py:243`) via `run_benchmark` (`benchmark.py:391`) |
| parent pool thread | `wait_result_broken_or_wakeup` (`process.py:416`) |
| parent QueueFeederThread | idle — everything already dispatched |
| all 12 workers | `queues.get()` (`process.py:242`) — **idle, awaiting new work** |

Every process idle: work was dispatched, workers completed it and returned,
and the results never reached the parent — the classic Windows
`ProcessPoolExecutor` lost-result deadlock (a worker dying while pickling a
result loses the payload without the pool noticing). The workers have already
released their results, so **nothing is recoverable**; the parent waits
forever. Confirmed idle by CPU sampling: **0.11 CPU-seconds across 16
processes over 60s**, no outbound sockets to either OpenRouter or
`memclaw.net`, ~30 minutes of log silence.

**Detection lesson: the monitor did not catch this.** It watched for 402s,
completion and process death — a hang is none of those. **Any monitor on a
long run must include a staleness check** (log mtime not advancing, or spend
not moving) or a hang reads exactly like slow progress. It cost ~30 minutes.

**Before spending another ~$29:** the structural problem is that
`run_benchmark` accumulates all five runs in memory and `cli.py` only writes
traces after it returns, so any failure at any point destroys everything. Two
runs have now been lost this way. Writing each run's trace as it completes
would make runs resumable and cap the blast radius — an upstream change, but
cheaper than repeatedly re-buying a full run. Lowering `--max-workers` reduces
pool pressure and probably the odds of the deadlock, at the cost of wall time.

**Also noted:** a separate GroupMemBench `baselines/memclaw` python process
(PID 5744) was running concurrently against `memclaw.net`, which plausibly
explains this run's 13 `504 Gateway Timeout`s from that service. Check for
competing local processes before a paid run — the Caura service is shared.

**Contamination measured before the hang: 28 recall failures / 2101 calls
(1.4%)**, of which 13 were `504`s from `memclaw.net` and **zero** were the
`no running event loop` race fixed in `9491888` — that fix held completely.

**Third default attempt 2026-09-10: self-contaminated, killed, $2.85 wasted.
Operational lesson worth more than the money.** The run was launched and
healthy, then the memclaw client was edited *while it was in flight* (an
MCP session-reuse rewrite). CL-Bench runs its workers in a **process** pool
(`concurrent.futures.process`), and every worker process spawned after the edit
imported the new module from disk. The run ended up executing a mix of two
client implementations, and `recall failed` jumped from **4/232 (1.7%)** to
**20/276 (7.2%)** — the tracebacks named `_CALL_TIMEOUT` and
`stack.enter_async_context`, symbols that exist only in the new code, which is
how it was caught.

**Rule: never edit a module a running job imports.** A thread pool would have
been safe (module already imported); a process pool is not. Anything touching
`src/systems/**` waits until no run is active, or goes in a branch/worktree the
run cannot see.

**The session-reuse rewrite itself was reverted** (working tree back to
`9491888`) and NOT committed, because the evidence for it collapsed under
testing: an apparent 1.5x speedup reversed when the benchmark order was swapped
(the second run of each pass was faster either way — warm-up, not design), and
neither client could be made to fail in isolation (0/150 concurrent calls each),
so the contamination fix it was built for could not be demonstrated either. It
remains a plausible mechanism — not tearing a session down per call cannot race
the teardown — but it trades a per-call failure mode for a shared one, and it is
not worth shipping into a paid study on mechanism alone.

**Second default attempt 2026-09-09 (later): died on real 402s at ~$6.55,
zero traces. The credits-vs-key-limit question is now settled by OpenRouter
itself**, which returned:

> `"This request would exceed your available credits given your current
> in-flight requests. Retry after in-flight requests settle, or add credits."`
> `code: 402, reason: in_flight_budget_exhausted,
> limit_source: openrouter_in_flight_budget,`
> `remedy_hint: "Adding credits ... raises your in-flight budget"`

Key headroom at the time was **$44.98**; the account balance was down to
**$1.79**. The key was never the constraint.

**Important refinement to the 2026-09-02 diagnosis: `in_flight_budget_exhausted`
has TWO inputs, and the fix only addressed one.** The per-request reservation
(`max_tokens`, now capped at 2048 — an 8x cut, verified working at 12 workers
when funded) is multiplied against concurrency and checked against an in-flight
budget **that itself scales with available credits**. So a well-capped run
still fails once the balance is low. The August failures at $46 balance were
reservation-driven; this one at $8 was credit-driven. Both must be right:
**cap the tokens AND fund the account.**

**Auto top-up did not fire** — `total_credits` sat at 1555.00 across the whole
run, from $8.34 down to $1.79. Do not assume it will rescue a run mid-flight;
confirm `total_credits` has actually increased before launching.

**The monitor did its job**: it detected the 402s and killed the run before
they could be written as completed-but-empty results. Keep that guard on any
paid run — it is the operational form of the standing contamination rule.

**Default-schedule attempt 2026-09-09: launched, killed at ~10%, $4.70 spent,
zero output.** Run group `memclaw-gpt54-default`. Launched against a $13.09
balance on a ~$28.80 projection, i.e. knowingly short; killed once it was clear
it would hit the wall around instance 283 of 624. **It wrote no trace files at
all** — verified: CL-Bench writes every trace within ~0.6s at the *end of the
invocation*, not per run (checked against `canary2-realkey`'s 13 files). So a
run that dies partway produces nothing, and there is no resume. **The only
viable shape is one uninterrupted pass with the full budget available up
front.** No credit errors were reached before the kill; the run was healthy.

**Do not confuse key headroom with credits.** The 2026-09-09 top-up raised the
key's spending limit ($22.98 -> $52.90) but added no credits, so spendable never
moved. OpenRouter enforces both and the account balance is the hard floor —
this is the same distinction behind the 2026-08-13 contamination. Key headroom
is now ample; credits are what is short.

**True cost measured 2026-09-09 with memory actually working: $0.04610 /
instance** (65 instances, run group `canary2-realkey`) — **3.2x the dead-key
figure**. The `default` schedule's 624 instances therefore project to
**~$28.80 for the memclaw arm**, and that is a floor: `quick_test` is 5 hands,
so recall can only ever return ~5 memories, while a 120-hand run returns a
full `top_k: 10` for most of its length. **Budget $35-40, not $9.**

**Second bug found and fixed the same day (ours, `9491888`).**
`memclaw_client._run` called `asyncio.run()` on the caller's thread; the
streamable-HTTP transport tears down background tasks as it exits and on a
benchmark worker thread that races the loop close, raising `RuntimeError: no
running event loop`. `system.py` catches it as "recall failed, continuing
without memories" — so the instance silently becomes a no-memory one and the
run still reports completed. **7 of 65 instances at 12 workers; 0 of 24 after
the fix**, which runs each call on a private thread. An offline self-check
ships with it (`python -m src.systems.memclaw.memclaw_client`, no key needed).

**Naming note:** the server now lists only `caura_*` tools. `memclaw_recall` /
`memclaw_write` still *resolve* identically when called, so the backward-compat
claim in the rebrand note holds for calls — but the MCP SDK logs `Tool
memclaw_recall not listed by server, cannot validate any structured content`
on every call. Cosmetic, and a lot of log noise to grep past.

**Stale credential found 2026-09-09 — `continual-learning-bench/.env` and
`STATE-Bench/.env` carry the same dead `MEMCLAW_API_KEY`** (`mc_UZc...JVMU`,
401), while `MemoryArena/.env` has a working one (`mc_lIQ..._auM`, 200). This
is the stale key HANDOFF.md flagged for STATE-Bench on 2026-08-18; CL-Bench
has been carrying it too, which is why the 2026-08-19 and 2026-08-26 CL-Bench
attempts may also have been memory-free regardless of how far they got.
CL-Bench's `.env` was repointed at the working key (old value backed up to the
session scratchpad) and verified 200. **`STATE-Bench/.env` is still on the
dead key** — it does not block the free #36 re-score, which makes no API
calls, but it blocks any STATE-Bench re-run.

**Budget measured 2026-09-09: $22.98 key headroom / $16.66 account balance.**
The key limit was raised since the 2026-09-01 note, so the **account balance is
now the binding constraint**. `clbench run` still has no resume, so a run that
exhausts the balance mid-schedule loses everything spent.

**The OpenRouter account is shared** across MemoryArena, CL-Bench and
GroupMemBench (byte-identical keys). Any two running large jobs concurrently
compete for the same pool and the same in-flight ceiling.

## CL-Bench: what is actually on disk here (2026-09-08)

Read the `results/` directory instead of trusting the status-table description,
which was wrong. Five trace groups, all 2026-07-28, all
`openrouter/openai/gpt-4o`, all `status: completed` with real per-instance
`reward` and `cost_usd`:

| trace group | system | schedule | runs | instances (incl. baseline phase) | cost | $/instance |
|---|---|---|---|---|---|---|
| `2026-07-28T11-14-40` | icl | quick_test | 3 | 20 | $0.17 | $0.0087 |
| `2026-07-28T11-16-59` | **memclaw** | quick_test | 3 | 20 | $0.61 | $0.0305 |
| `2026-07-28T11-26-31` | icl | **default** | **5 × 120** | 624 | $5.20 | $0.0083 |
| `2026-07-28T13-08-10` | **memclaw** | quick_test | 3 | 20 | $0.57 | $0.0287 |
| `2026-07-28T14-14-45` | **memclaw** | quick_test | 6 | 35 | $1.16 | $0.0331 |

Two things follow, and they change the plan:

1. **The integration ran end-to-end on 2026-07-28**, not first on 2026-08-19 as
   the section above says. Those are completed memclaw runs with rewards, from
   a working tree a day before the integration commit. The 08-19 note is still
   right about substance — `quick_test` is 5 hands × 3 runs and cannot resolve
   poker variance — but "the first time it ever executed" is not accurate.
2. **There is already a completed `icl` control on the full `default` schedule
   at gpt-4o.** At the measured $0.031/instance for memclaw, a matching memclaw
   `default` run is **~$19** and would be the first citable CL-Bench pair. The
   gpt-5.4 plan (`configs/poker/memclaw.json`) exists to sit alongside upstream's
   shipped `mem0-gpt-5.4`/`ace-gpt-5.4`/`icl-gpt-5.4` leaderboard baselines; the
   2026-08-26 attempts at that tier burned ~$14 and finished nothing.

**Recommendation: run the gpt-4o pair first.** It is cheaper, its control is
already on disk and paid for, and it produces an internally-consistent result
instead of a fourth failed gpt-5.4 attempt. It will **not** be comparable to
upstream's leaderboard — that comparison still needs the gpt-5.4 arm — so say
"memclaw vs our own icl control at gpt-4o", never "vs the CL-Bench leaderboard".

Unlike STATE-Bench, **CL-Bench does track per-instance `cost_usd`**, so this is
the one benchmark here that can carry a real cost/token comparison.

## GroupMemBench: memclaw baseline (2026-08-19)

Built on the other machine, mirroring the existing RAG baselines' structure:
`baselines/memclaw/{memclaw_client.py,eval_benchmark.py,run_eval.sh}` plus a
`memclaw)` case in the top-level `run_eval.sh` dispatch.

**Two real bugs found before anything ran:**

- The first draft used a **REST** client, copying
  `memclaw-benchmarks/runners/memclaw_client.py`'s own unverified guess. Wrong.
  MemClaw is an **MCP server** (`https://memclaw.net/mcp`, `X-API-Key`,
  `memclaw_recall`/`memclaw_write`, `filter_agent_id` for isolation) — as
  MemoryArena's and CL-Bench's working integrations both show. **This means
  `runners/memclaw_client.py` in THIS repo is very likely wrong too.** It was
  kept when Track B was deleted because `recall_accuracy.py` depends on it —
  and since LoCoMo/LongMemEval are now dropped, nothing will ever exercise it.
  Flagged, not fixed.
- `MEMCLAW_API_KEY`/`MEMCLAW_MCP_URL` were read as module-level constants at
  import, before `load_env_file()` runs in `main()` — always empty in practice.
  Fixed to resolve lazily.

**Full-scale ingest is not feasible as built.** Finance alone has **30,000
messages**; measured MemClaw write latency is **~2.3s/call sequential** (each
call opens its own MCP session; no batching tool exists) → **~19 hours per
domain**. Confirmed by timing 480 real writes at 18m55s, matching the estimate
almost exactly. **"As built" is the operative phrase — see "Ingest throughput:
SOLVED" below: the per-call session teardown is most of that 2.3s, and dropping
it plus ×16 concurrency measures at ~1.3h/domain. Do not cite the 19h figure as
a current blocker.**

**Ran a fair smoke-scale 3-way instead** — truncating *all three* baselines
equally to the first 80 messages/channel (480 total) of Finance, same 8
`multi_hop` questions, rather than letting memclaw see a fraction of what the
RAG baselines get in full:

| baseline | accuracy (n=8) |
|---|---|
| bm25 | 1/8 |
| text-embedding-3-large | 0/8 |
| memclaw | 1/8 |

**A wiring check, not a benchmark result** — n=8 on a deliberately truncated
haystack where most questions' evidence is absent for *every* baseline.

### Ingest throughput: SOLVED, measured 2026-09-02 — ~19h/domain → ~1.3h

~~**Open question before a real run**: closing the 30k-message gap needs either
parallel ingest (untested — MemClaw's per-tenant rate limits under concurrency
are unknown) or accepting a multi-hour background job per domain.~~ **Answered.**

Measured directly against production `https://memclaw.net/mcp` from this
machine (probe script in that session's scratchpad, not checked in — ~40 lines,
trivial to rewrite: N `memclaw_write` calls under varying session/concurrency
strategy, timed). **720 writes across 9 conditions, 0 errors, concurrency 1
through 64. No rate limiting was observed at any level.** Cost **$0** — this
hits Caura's own service, which bills none of the LLM providers, so it was
runnable while OpenRouter was blocked.

**Two independent levers, and they stack:**

| condition | writes/s | 30k msgs |
|---|---|---|
| A seq, session-per-call *(what the baseline does today)* | 0.21 | 40.1h |
| B seq, **shared session** | 0.52 | 16.2h |
| C par ×4, session-per-call | 0.65 | 12.8h |
| D par ×8, session-per-call | 0.99 | 8.4h |
| E par ×16, session-per-call | 1.34 | 6.2h |
| F par ×8, **shared session** | 3.23 | 2.6h |
| **G par ×16, shared session** | **6.21** | **1.34h** |
| H par ×32, shared session | 1.98 | 4.2h ⚠️ outlier |
| I par ×64, shared session | 8.86 | 0.94h |

1. **MCP session reuse is the bigger surprise and the cheaper fix.** Median
   latency is **4.05s session-per-call vs 1.42s on a shared session** — roughly
   **2.6s of every write is MCP session setup**, not the write. `MemclawClient`
   (in `MemoryArena/memory/memory_systems/memclaw_client.py`, which the
   GroupMemBench baseline was modelled on) opens and tears down a session
   *per call* — that is the actual bottleneck, and fixing it needs no
   concurrency at all. **2.5x for free, zero rate-limit exposure.**
2. **Concurrency then stacks ~12x on top of that**, to 6.21 writes/s at ×16.

**Recommend ×16 on a shared session (~1.3h/domain, ~5.4h for all four).**
Not ×64: the curve is not clean — the ×32 row (1.98 writes/s) is *slower than
both ×16 and ×64*, which at n=80 is only ~2.5 waves and reads as a transient
blip rather than a real saturation point. Everything above ×16 is unreliable
enough that quoting a precise optimum would be overclaiming. ×16 is comfortably
on the measured-safe part of the curve.

**Write→searchable lag is NOT a problem here — checked explicitly, because it
is exactly what makes mem0's arm weak** (see the async-ingestion caveat in the
mem0 setup section). 8 memories written concurrently were **all 8 recallable
2.0s after the writes were accepted** (t+4.7s from batch start). Unlike mem0,
Caura has no async fact-extraction lag to design around.

**Two caveats, stated plainly:**

- **The recorded 2.3s/call figure did not reproduce.** Sequential
  session-per-call measured **4.05s median** here, ~1.8x slower, so this
  machine's "40h/domain" and the 2026-08-19 machine's "19h/domain" disagree on
  absolutes. Different machine, different network, different day. **The
  relative speedups (2.5x session reuse, 12x concurrency) are the reliable
  part; treat the absolute hours as this-machine estimates.**
- ~~**The fix cannot be applied from this checkout.**~~ **STALE — corrected
  2026-09-13. `baselines/memclaw/` IS here** (`memclaw_client.py`,
  `eval_benchmark.py`, `run_eval.sh`), and **the fix is already applied**: the
  client defaults to `https://caura.ai/mcp`, holds ONE shared MCP session on a
  private loop thread, and bounds concurrency with a semaphore at 16 — exactly
  the measured-optimal configuration below. Its own header cites the 2026-09-02
  measurement. `data/final/` confirms the scale (**30,000 messages per domain,
  120,000 writes total**). Nothing needs pulling over and nothing needs editing;
  drop it from the Next action item 4 list.
- **`eval_benchmark.py --ingest-only` exists and is genuinely free** — verified
  by reading the code path: it returns immediately after `ingest(...)`, before
  any chat client is constructed, so the ingest half costs **$0** and can run
  while OpenRouter is blocked. Invocation used 2026-09-13:
  `python baselines/memclaw/eval_benchmark.py --conversation-json
  data/final/Finance/... --questions-jsonl "" --output-jsonl results/... 
  --agent-id gmb-finance --ingest-concurrency 16 --ingest-only`

**Remaining blocker for a real run is no longer throughput — it is the
question-answering LLM spend**, which is on the shared OpenRouter account and
therefore behind the same key-limit gate as everything else.

## TOOL-LOOP ROBUSTNESS RUN: ✅ COMPLETE (phys, 2026-09-13) — the effect survives but HALVES

Next-action item 0/0b is **done for phys**. `phys_gemini36_toolloop` is 20/20 in
both arms with the agent tool loop actually working (`MATH_ENABLE_TOOL_LOOP=1`),
against **708/708 subtasks failing the tool loop** in every other result in this
file. Same 20 papers, same `gpt-4o-mini` judge, same agent model — the *only*
difference is the agent code path.

| phys @ gemini-3.6-flash | memclaw | none | gap | perm p | subtask McNemar | wins |
|---|---|---|---|---|---|---|
| broken path (single-shot) — every published number | 55.90% | 31.76% | **+24.14pp** | 0.0013 ✅ | 4.2e-07 ✅ | 12-1-7 |
| **working tool loop** | **47.01%** | **34.26%** | **+12.75pp** | 0.0867 ❌ | **0.0118** ✅ | 8-2-10 |

**The gap roughly halves, and both arms move toward each other**: memclaw drops
8.89pp while `none` *rises* 2.50pp. A working tool loop lets the no-memory agent
recover some of what it previously needed memory to supply. This is the
"headroom" argument with the judge confound controlled — same ruler, same tier,
only the code path differs — which is exactly what the gpt-5.6-sol re-judge
could not isolate.

**Read it honestly, in both directions.** Subtask correctness (86 observations)
still clears significance comfortably at p=0.0118 — memory still helps. But the
paper-level progress score no longer does, and **anyone who fixes the tool loop
will measure roughly half the gap this file publishes.** That is the objection
item 0 existed to pre-empt, and the answer is "smaller, still there", not
"unchanged". Do not quote +24.14pp externally without noting the tool loop was
inoperative when it was measured.

**n=20 cannot resolve +12.75pp** — 95% CI [0.25, 25.67]pp. Do NOT read p=0.0867
as "the effect disappeared"; read it as "this sample cannot resolve it". **Math
is the test that can** (40 papers / 354 subtasks): `math_gemini36_toolloop` is
at memclaw 5/40, none 0/40, configs exist, ~$6-8. Until math runs, the halving
is one domain at small n.

### The 1/86 empty response is real, reproducible, and changes nothing

`memclaw/0000.0003` subtask 0 returns an empty response with **0 tool calls**
after ~137-262s, `error: None`, `step: 1`. Re-run 2026-09-13 from a clean
quarantine: **it reproduced exactly** — this is a deterministic tool-loop
failure mode, not transient flakiness, so re-running it again is wasted money.
The `none` arm answers the same subtask normally (2965 chars, 1 tool call), so
the prompts differ only by memclaw's `<memory_context>` wrapper carrying
`Initial result: Empty` — the subtask-0 baseline-offset issue noted under the
2026-08-03 diagnostics, biting in the other direction.

**Zero impact on the comparison: all three subtasks of that paper score wrong in
BOTH arms, so the paper is a tie either way.** Verified by scoring with and
without it — identical to four decimal places. The arm still flags
`CONTAMINATED (1.2%)` on the scanner; that flag is correct and should stay, but
it is not a reason to withhold the result. Old copy quarantined at
`_empty_backup_20260913/`.

### `scripts/paired_stats.py` was scoring quarantine folders as arms

The `_`-prefix exclusion this file claims was added 2026-09-10 **was never
actually in the code** — `arm_dirs` was a bare `os.listdir` + `isdir`, so
`_empty_backup_20260909` was loaded and compared as a real arm. Fixed
2026-09-13 (one line); verified the 4-arm `phys_gemini36` dir still discovers
letta/mem0/memclaw/none. A reminder that "fixed" in these notes is worth
re-verifying against the source before relying on it.

### MATH TOOL-LOOP: interim 16-paper result (2026-09-14) — the phys halving does NOT replicate so far

Ran overnight 2026-09-13/14, stopped on budget at **memclaw 38/40, none 16/40**.
Both arms scan clean (0/341 and 0/125 empty). `paired_stats.py` scores the
**16 papers in common**.

| metric | memclaw | none | test | p |
|---|---|---|---|---|
| progress score (16 papers) | 32.44% | 25.69% | +6.75pp, 95% CI [-1.38, 15.13] | perm **0.148** ❌ |
| subtask correctness (125 subtasks) | 18 own-only | 9 | McNemar exact | **0.122** ❌ |
| paper passrate | 2/16 | 3/16 (1 vs 2 discordant) | McNemar exact | **1.0** ❌ |

Per-paper wins: memclaw 8, none 4, tied 4.

**The headline comparison:**

| domain | broken path | working tool loop | change |
|---|---|---|---|
| phys (n=20) | +24.14pp | +12.75pp | roughly halves |
| **math (n=16, INTERIM)** | +7.76pp | **+6.75pp** | **barely moves** |

If this holds at n=40, **"fixing the tool loop halves the effect" is a
phys-specific finding, not a general one** — which changes what has to be
disclosed externally. **It is NOT citable yet:**

1. n=16, nothing significant. The broken-path math result hit p=0.0006 at n=40;
   a similar effect here sits at p=0.148 on sample size alone.
2. **The 16 papers are not a random subset.** Both arms walk a deterministic
   paper order, so these are the *first* 16 — systematically, not randomly,
   chosen. A subset effect cannot be excluded.
3. Paper passrate nominally favours `none` (2 vs 3), but that metric is
   final-subtask-only and has almost no resolution at this n.

**To finish: the `none` arm needs 24 more papers (~$53).** memclaw needs only 2,
and **those 2 are worthless until `none` catches up** — see the arm-order trap
below.

### ⚠️ `usage.json` CANNOT SEE TOOL-LOOP SPEND — do not budget from it

**Measured 2026-09-14: 7 papers showed $2.89 of agent tokens in `usage.json`
while the OpenRouter balance fell $15.47.** `usage.json` is ~19% of true cost
on a tool-loop run.

Cause: `OpenAIBackend.chat` accumulates `response.usage` (`llm_backend.py:124-127`),
but `agent/math.py::_act_with_tools` builds its **own** `OpenAI` client and calls
`client.chat.completions.create` directly, bypassing that accounting entirely.
On a tool-loop run the bypassed traffic IS the dominant cost.

**True measured cost, gemini-3.6-flash tool loop: ~$2.21/paper** ($15.47 / 7
papers), i.e. **~$88 for a full 80-paper pair** — not the $6-8 in Next action
item 0b, and not the $0.38/paper that `usage.json` implies. **Always budget from
the OpenRouter balance delta, never from `usage.json`.**

### ⚠️ ARM ORDER IS BACKWARDS UNDER A BUDGET CONSTRAINT

`run_toolloop_phys.sh` runs `memclaw` to completion, *then* `none`.
`paired_stats.py` scores only papers present in **both** arms, so once memclaw
is ahead, **every further memclaw paper adds nothing to the scoreable set.**

On 2026-09-13/14 this wasted roughly $15: seven memclaw papers (32→38) were
bought while `none` sat at 16, so none of them entered the comparison. **When
budget is the constraint, run the LAGGING arm** — or interleave.

### Math tool-loop run, 2026-09-13 — cost/throughput reprojection (IMPORTANT)

**The "~$6-8 for the math tool-loop pair" estimate in Next action item 0b is
WRONG and should not be used.** It was extrapolated from single-shot-path runs.
The tool loop makes several LLM calls per subtask by design, so per-paper cost
is several times the broken-path baseline.

Measured on this machine 2026-09-13, gemini-3.6-flash, memclaw arm:

| quantity | measured |
|---|---|
| subtask throughput | ~3.9 min/subtask (31 subtasks / 122 min) |
| paper throughput | **~45 min/paper** (3 papers / 2h15m) |
| spend rate | **~$1/hour** ($2.08 over 2h07m) |
| per paper-attempt | **~$0.52** (includes failed papers' wasted retries) |

So the remaining **41 papers project to ~10-15 hours and ~$20**, not $6-8.
Budget a full math tool-loop pair from scratch (80 papers) at **$35-40**.

**Three papers failed on transient causes, all on the memclaw arm** — DNS
`getaddrinfo failed`, a 300s read timeout on the local memory server, and a
`500` on `/memory/add`. `none` uses `NullMemoryClient` and never touches the
memory server, so **this failure class is inherently asymmetric**. Failed papers
leave no directory (verified) and are reclaimed free by a second pass, but if
any paper fails repeatedly on memclaw only, the arms end up with different paper
sets and `paired_stats.py` silently scores the intersection. Record per-arm
paper counts with every tool-loop result.

Caura itself was healthy throughout — a 15-write probe returned **15/15 at 4.78s
median**, so those were transient spikes, matching the 2026-08-27 read.

**Two MemoryArena runs were briefly active at once** (an earlier `none`-arm job
from 17:52 plus a newly launched pair), which would have put two writers on the
same `result.jsonl`. Killed the older one. **Check for an existing `run_math.py`
process before launching — the run scripts do not.**

### Operational notes from this run

- **`pgrep -f` from Git Bash cannot see Windows processes either** (confirmed
  2026-09-13: `pgrep -f run_math.py` found nothing while PowerShell saw 2). A
  liveness check built on it reports a false death. Prefer **log-mtime
  staleness** over any process check — platform-independent, and it is what
  actually catches a hang. Threshold must be generous: a single tool-loop paper
  stalled ~35 min inside one `ssl.read` and then recovered, so 30 min
  false-fires. Use 90 min.
- **`kill -0 <pid>` from Git Bash cannot see Windows PIDs** and returns "dead"
  for a live process. A wait loop built on it reports a false death and will
  make you think a healthy run has crashed. Use
  `powershell Get-Process -Id <pid>` instead.
- The memory server on :8000 was **already running** from earlier in the day; a
  second one fails to bind with `WinError 10048` and exits, which is easy to
  misread as the server being down. Check `netstat` before starting one.
- Smoke-tested recall by **content** before running (per the standing rule):
  `/memory/wrap_user_prompt` takes `question`, not `user_prompt`, and returned
  the stored fact inside `<memory_context>`. caura.ai endpoint healthy.
- Cost: **~$0.05** (one 3-subtask paper).

## Competitor arms beyond mem0: letta ✅ runnable, zep ⛔ excluded (2026-09-10)

`MemoryArena`'s harness supports far more memory systems than this file ever
recorded. `memory/memory_systems/` implements **letta, zep, mirix, amem,
lightmem, graphrag, memorag, reasoningbank, rag (text-embedding) and
long_context** alongside mem0 and memclaw, and configs already exist for
`phys_{letta,zep}_gemini36` and a whole **`gemini-3.8-flash` tier**
(`phys_{memclaw,none,letta,zep}_gemini38`). **No results exist for any of
them.** Keys for both (`LETTA_API_KEY`, `ZEP_API_KEY`) are in `MemoryArena/.env`
and both SDKs (`letta_client`, `zep_cloud`) are installed.

The letta/zep gemini36 configs write into **`./results/json/phys_gemini36`** —
the same directory as the published memclaw/none/mem0 arms, same 20 papers,
same `gpt-4o-mini` judge — so running them extends the existing comparison to
five arms rather than creating a new one. Verified flattened-identical to
`phys_memclaw_gemini36.json` except `memory_system_name`.

**Both integrations work at the API level.** Controlled test (fresh `user_id`,
write, wait 30s, `wrap_user_prompt`): memclaw and letta both returned the stored
fact; zep returned an empty `<memory_context>`.

**⛔ letta is blocked on a PLAN LIMIT, not a bug — attempted 2026-09-10, 3/20
papers.** The run failed 17 of 20 papers with `500` from the local memory server
on `/memory/initialize`. Root cause, from calling `LettaMemorySystem` directly:

> `402 Payment Required — "You have reached your limit for agents, please
> upgrade your plan or delete some agents", limit: 3`

`MemoryClient.__init__` creates **one Letta agent per paper**, and the free plan
caps the account at **3 live agents**. So papers 1-3 ran and every later one
402'd. The 3 completed papers were quarantined at
`results/json/phys_gemini36/_letta_partial_3of20_20260910/`. **The reason given
at the time was wrong** — I claimed `paired_stats.py` "loads every subdirectory
as an arm", but it did not: it hardcoded `("memclaw", "mem0", "none")` and would
have ignored a letta arm entirely. Quarantining was still correct practice
(a partial arm should never sit in a scored directory), just not for the stated
reason. The `_`-prefix is now a real exclusion rule — see the arm-discovery fix
below.

**✅ FIXED 2026-09-10, free, no plan upgrade.** `memory/memory_systems/letta.py`
now recovers from the cap instead of dying on it: when `agents.create` returns
the limit error, it retires the **oldest** agents on the account and retries
once (oldest-first, since the newest may belong to a run still in progress).
Chosen over repairing the existing `_OWNED_AGENTS` tracking because that
tracking is what silently failed — recovering at the point of failure works
regardless of why. Validated by reproducing the exact failure: five sequential
creations with the owned-agent tracking cleared each time, which previously died
at the fourth, now all succeed.

**Before re-running: restart the memory server** (port 8000). It imports this
module at start, so a server launched before the fix keeps the broken version —
the same class of trap as the mem0 key note above.

**The smoke test did not catch this** because it created a single agent. A
credential/API smoke test proves one call works; it does not prove a 20-paper
run works when the provider meters a *resource* rather than a rate. For any new
memory system, check what the plan limits per account, not just whether one
call returns 200.

**⛔ zep is excluded on ingestion latency, not on quality.** Measured directly
(`zep_latency.py`, write then poll every 15s): **20 polls over 309 seconds, the
fact never became searchable** — though the same write was visible after ~10
minutes in an earlier test. **Phys subtasks run roughly every 18 seconds**, so
zep would almost never have memory available when the next subtask asks. Its
arm would score like the no-memory control and produce a large, entirely
artifactual "Caura beats zep" result. **Do not run it and quietly report the
number.** The latency is the finding: report zep as excluded because its
write→searchable lag exceeds five minutes, which rules it out for turn-by-turn
agent memory at this cadence.

**Attempted fix, and why it failed — record this so nobody retries it.** The
integration writes with `thread.add_messages()` and reads with
`graph.search(scope="edges")`, i.e. it writes to a conversation thread and reads
from the knowledge graph, which is populated by async entity/edge extraction.
The obvious fix was zep's intended agent path, `thread.get_user_context()`.
**Tested: it is gated on the same extraction.** Both retrieval paths polled every
10s for 106s after a write returned `thread_context=empty  graph_edges=0`
throughout (`zep_cloud` 3.28.0). A `graph.add(type="text")` variant is already
commented out in `add_chunk`, so a previous attempt evidently went the same way.

So this is **architectural, not an integration defect**: zep requires graph
extraction to finish before anything is retrievable by any of its APIs. Nothing
at the client layer fixes it. The remaining options both invalidate the
comparison — slowing the benchmark for one arm only, or pre-ingesting all memory
before the run, which defeats the sequential-learning design the benchmark
measures.

This is the mem0 async-ingestion caveat (see the mem0 setup section) but far
more severe — mem0 was ~30s, zep is >5min.

**Method note this reinforces: smoke-test recall CONTENT, never status codes.**
`initialize`, `add` and `wrap_user_prompt` all returned **200 for both systems**
while neither recalled anything. A run launched on that evidence would have
completed, exited 0, and produced a favourable-looking result built on arms
that had no memory at all.

## phys gemini-3.6-flash, FOUR arms (2026-09-10) — letta TIES Caura

The letta arm completed 20/20 after the agent-cap fix. All four arms are the
same 20 papers, same `gpt-4o-mini` judge, same single-shot code path
(`MATH_ENABLE_TOOL_LOOP=0`), and **all four scan clean at 0/86 empty
responses**.

| arm | progress score | paper passrate |
|---|---|---|
| **memclaw (Caura)** | **55.90%** | 11/20 |
| **letta** | **55.35%** | 11/20 |
| mem0 | 41.01% | 7/20 |
| none | 31.76% | 5/20 |

**Caura vs letta is a tie on every metric — report it that way.**

| comparison | progress score | perm p | subtask McNemar | wins |
|---|---|---|---|---|
| memclaw vs letta | +0.56pp, 95% CI [-8.33, +8.89] | **0.8909** ❌ | 9 vs 7 own-only, **0.8036** ❌ | 5-3-12 |
| memclaw vs mem0 | +14.89pp | **0.0311** ✅ | 22 vs 4, **0.0005** ✅ | 10-2-8 |
| memclaw vs none | +24.14pp | **0.0012** ✅ | 26 vs 1, **0.0000** ✅ | 12-1-7 |
| letta vs mem0 | +14.33pp | 0.0506 | 20 vs 4, **0.0015** ✅ | 9-2-9 |
| letta vs none | +23.58pp | **0.0032** ✅ | 25 vs 2, **0.0000** ✅ | 11-1-8 |
| mem0 vs none | +9.25pp | 0.1736 ❌ | 9 vs 2, 0.0654 ❌ | 5-2-13 |

**The correct claim is `Caura ≈ letta > mem0 ≈ none`, NOT "Caura beats
competing memory systems".** letta's margins over mem0 and no-memory are within
noise of Caura's own. Anyone who runs letta will find this, so publishing the
weaker claim is both honest and the only defensible option.

What this does NOT change: Caura vs no-memory (+24.14pp) and Caura vs mem0
(+14.89pp) are untouched and still significant. The memory-helps finding stands;
the memory-system-ranking claim narrows to "beats mem0, ties letta".

**One caveat on letta's arm, stated plainly:** letta's own agent runs an LLM
during `add_chunk` (it reasons before storing), so its arm is not a pure
memory-store comparison the way mem0 and Caura are — some of letta's score may
come from that extra inference rather than from recall. Its `LETTA_MODEL`
defaults to a BYOK handle, billed outside the OpenRouter account this file
tracks. Worth measuring before leaning on the tie in any external writeup.

**`scripts/paired_stats.py` hardcoded its arm list** (`memclaw`, `mem0`, `none`)
and would have silently omitted letta from the output entirely — a complete
20/20 arm sitting on disk, loaded by nobody. Fixed 2026-09-10: arms are now
discovered from the directory, all pairs compared, `_`-prefixed directories
excluded as the quarantine convention. **A comparison you cannot see is worse
than one you have not run.**

## ⚠️ THE MCP ENDPOINT MOVED: memclaw.net → caura.ai (2026-09-11)

**`https://memclaw.net/mcp` is dead. The service is at `https://caura.ai/mcp`.**
Verified end to end: `caura_write` 200, `caura_recall` returns the stored fact,
12 tools listed, same `MEMCLAW_API_KEY` accepted on both `X-API-Key` and
`Authorization: Bearer`. The old `memclaw_*` tool names still resolve when
**called**; they are simply absent from `tools/list`.

**This corrects the rebrand note at the top of this file.** "URLs keep working
for backward compatibility" is **no longer true** for the MCP host. Tool names
still alias; the hostname does not.

**It also nearly caused a false bug report.** For ~8.5 hours this was diagnosed
as a Caura outage — `/memory/add` returning 500, `curl https://memclaw.net/mcp`
returning 000, `SSL: UNEXPECTED_EOF_WHILE_READING` on direct calls — and a Slack
message to the Caura team was drafted and very nearly sent. The user asked
"memclaw was renamed to caura, can we check with caura" and one probe settled
it: `https://caura.ai/mcp` answered **401** (auth required) where memclaw.net
answered **000** (connection refused). A dead host and a live host that wants a
key look nothing alike once you actually compare them.

**The lesson, and it is not a small one:** every symptom was consistent with an
outage, and the conclusion was still wrong. When a service "goes down" right
after a product rebrand, check whether it moved before reporting it broken —
and check the *vendor's current domain*, not only the one in your config. The
`tools/list` returning only `caura_*` had already been noted in this file as
"cosmetic"; it was in fact the visible edge of a migration.

### Fix applied — config only, no code change

All three clients already read `MEMCLAW_MCP_URL` and default to the dead host
(`MemoryArena/memory/memory_systems/memclaw_client.py:25`,
`continual-learning-bench/src/systems/memclaw/memclaw_client.py`,
`STATE-Bench/agents/memclaw_agent.py:33`). So the fix is one line per `.env`:

    MEMCLAW_MCP_URL=https://caura.ai/mcp

Added to **all three** `.env` files 2026-09-11. GroupMemBench's
`baselines/memclaw/` is on the other machine and **still needs the same line**.

**The memory server must be restarted after changing it** — it reads the URL at
import, so a server started before the change keeps talking to the dead host.
Restarted and verified: initialize 200, write 200, recall returns the fact.

**`STATE-Bench/.env`'s key swap is now verified too** — the 2026-09-11 swap to
`mc_lIQ..._auM` could not be checked when made because it was tested against the
dead host.

### What this unblocks

Nothing was ever wrong with Caura's service, and nothing is blocked on it. The
two ~$3 re-runs (Opus phys 3 papers, `gpt-5.6-sol` replicate) and the math
tool-loop pair's memclaw arm are all blocked **only on OpenRouter key headroom**
($1.43 as of 2026-09-11).

**Still true and worth keeping:** the earlier reliability observations stand on
their own evidence — 13 × `504 Gateway Timeout` from the service under 12-way
concurrency on 2026-09-10 (counted in that run's log), and the Opus phys papers
lost to `caura_write` 500s on 2026-08-27 (recorded at the time; no artefact
survives, since failed papers leave no directory). Neither is explained by the
move.

## Cross-repo context

- `continual-learning-bench` (sibling directory) is where MemClaw was wired
  in as an evaluated "system" for CL-Bench specifically — that repo's own
  harness, not this one.
- This repo (`memclaw-benchmarks`) is the standalone suite for
  dataset-driven QA benchmarks (LoCoMo, LongMemEval, and now STATE-Bench,
  MemoryArena-Rotation, GroupMemBench). Keep benchmark-specific scaffolding
  here unless a benchmark's own harness forces a different integration point
  (as CL-Bench did).
- **The old Track B suites (keystone enforcement, multi-agent transfer, trust
  tiers, contradiction convergence, fleet-scale compounding) were removed
  2026-08-04** — `suites/{keystone_enforcement,multi_agent_transfer,trust_tier_access,contradiction_convergence,fleet_scale_compounding}/`,
  their `datasets/custom/*.json` fixtures, and `judges/assertions.py` are all
  deleted from the codebase (recoverable via git history if needed). The
  README no longer describes a "Track A/B" split — it's just the recall-
  accuracy suites (LoCoMo/LongMemEval) plus the MemoryArena-Rotation summary
  now. `runners/harness.py` and `runners/memclaw_client.py` were kept — Track
  A's `recall_accuracy.py` depends on both, so they weren't Track-B-only
  despite living alongside the deleted suites.

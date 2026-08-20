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
| CL-Bench | ✅ run (quick_test) | `continual-learning-bench` repo (sibling dir) | MemClaw integrated as a `system` (`src/systems/memclaw/`) on branch `add-memclaw-system`, following the same retrieve-then-respond/store-after-observe pattern as the `mem0` baseline system. A quick_test run happened, but on a different machine/worktree — **not visible from this checkout**: as of 2026-07-31 this clone has no memclaw config under `configs/`, and nothing in `results/`/`final_results/` is dated after the integration commit (2026-07-29). Results/logs need to be pulled over from wherever that run actually happened before they can be cited here. |
| STATE-Bench | ⏸️ on hold | `STATE-Bench` repo (sibling dir), cloned | MemClaw agent adapter (`agents/memclaw_agent.py`) exists but blocked: the eval protocol (`state_bench/configs/eval_protocols/gpt54.json`) locks the user-simulator + judge to GPT-5.4 via Azure OpenAI only (no OpenAI/OpenRouter path — `client.py`'s `_build_openai_client` explicitly rejects any custom `base_url`, and the eval client has no non-Azure code path at all). We only have an OpenRouter key, which can cover the agent side (via a custom `BaseLLMClient`/`BaseAgent` subclass under `clients/`/`agents/`) but not the locked judge/simulator. Need an Azure OpenAI resource with a GPT-5.4 deployment before resuming. If unblocked, only the **Agent Learning Track** (train-trajectory learning transfer, `docs/AGENT_LEARNING_TRACK.md`) is worth running — the main track doesn't exercise memory. |
| MemoryArena-Rotation (travel) | ✅ **settled — negative result, do not re-run** | `MemoryArena` repo (sibling dir), cloned | See "MemoryArena travel: settled" section below. memclaw vs no-memory are statistically indistinguishable at n=50 groups, and the benchmark is too small to ever resolve the observed effect. Travel is closed unless the agent model changes. |
| MemoryArena-Rotation (math) | ✅ **significant win at gpt-4.1** (memclaw vs none); mem0 arm ✅ **run 2026-08-04 on a second machine — mem0 ≈ none, memclaw beats both**; ✅ **gemini-3.6-flash tier complete 2026-08-19** (memclaw vs none significant, +7.76pp progress score, subtask McNemar p=0.0007 — replicates phys at this tier; mem0 comparison softer than gpt-4.1's, not a clean "mem0≈none" repeat — see "MemoryArena math: gemini-3.6-flash — complete" below) | `MemoryArena` repo, `run_math.py` + `configs/formal_reasoning_configs/math_memclaw_gpt41.json` / `math_none_gpt41.json` / `math_mem0_gpt41.json` (+ `*_gemini36.json` variants) | Self-contained (HF dataset `ZexueHe/memoryarena`, config `formal_reasoning_math`): **40 papers / 354 subtasks**. gpt-4o-mini run (2026-08-02) was directional but underpowered; gpt-4.1 rerun (2026-08-04) cleared significance on all three metrics — see "MemoryArena math: gpt-4.1 rerun" below. mem0 arm completed same day on a second (higher-RAM) machine after the primary machine OOM'd — see "MemoryArena math: mem0 arm result" below. ~18s/subtask → ~106 min sequential, ~27 min at 4 shards. See "MemoryArena math: setup gotchas" below — several traps cost real time. Math has **no token/cost tracking at all** (`formal_reasoning_env/llm_backend.py`'s `OpenAIBackend.chat` returns only text, never reads `response.usage`), so the travel zero-usage fix doesn't apply and spend must come from OpenRouter's key API. It also runs an **LLM judge** through OpenRouter (`env_config.model_name`), billing roughly double per subtask. Resumable per-paper via `_is_paper_processed`. Note: `results/json/math_gpt5mini/` holds an **abandoned partial run** (2 papers, memclaw only, no logs) from a `math_memclaw_gpt5mini.json`/`math_none_gpt5mini.json` config pair found already in the repo but never mentioned in this file before 2026-08-04 — origin unknown, not part of any tracked result, safe to ignore or resume separately. |
| MemoryArena-Rotation (phys) | ✅ **significant win at gpt-4.1 — stronger than math** (memclaw vs none); mem0 arm ✅ **run 2026-08-05 — mem0 ≈ none, memclaw beats both**; ✅ **replicated at `google/gemini-3.6-flash` 2026-08-12 with a larger effect** (+24.14pp, subtask McNemar p=4.2e-07); ✅ **gemini mem0 arm run 2026-08-20 — memclaw still wins (progress score p=0.035, subtask p=0.0005), mem0 vs none trends positive but not significant (p=0.17), matching the same soft trend seen in math-gemini** | `MemoryArena` repo, `run_math.py` + `configs/formal_reasoning_configs/phys_memclaw_gpt41.json` / `phys_none_gpt41.json` / `phys_mem0_gpt41.json` (+ `*_gemini36.json` variants) | Second formal-reasoning domain, run as a replication of the math gpt-4.1 result. **20 papers / 86 subtasks**, same infra as math (shares `MathEnvironment`/env server/judge). See "MemoryArena phys: gpt-4.1 replication" below — effect is larger and cleaner than math despite half the sample (progress score +20.46pp vs +4.92pp, subtask McNemar p=0.0003 vs p=0.031). memclaw won every paper it didn't tie (9-0-11), none never won one. mem0 arm ran 2026-08-05 at `-Shards 1` on this machine and replicates math's mem0 finding — see "MemoryArena phys: mem0 arm result" below. **All three arms of both formal-reasoning domains are now complete at both gpt-4.1 and gemini-3.6-flash tiers.** |
| MemoryArena-Rotation (shopping) | ⛔ blocked on a large data download | `MemoryArena` repo, `run_shopping.py` + `configs/web_shopping_configs/memclaw.json` | Not runnable as-is: `data/shopping/` does not exist in this checkout and the config points at it (`upstream_webshop_data_root`). Needs the product DB from <https://huggingface.co/datasets/ai-hyz/MemoryArena-product-db> (`items_shuffle.json`, `items_ins_v2.json`, `domain_data.json`, a pyserini `search_engine/indexes-full/` index, `product_catalog/`), **plus** a JDK on `PATH` for the search engine and `pip install -r env/env_systems/web_shopping_env/requirements-shopping.txt` + `python -m spacy download en_core_web_lg`. It also boots a separate upstream WebShop service on port 36004. Do this setup deliberately — it is much heavier than travel/math. |
| GroupMemBench | ⏳ queued | not started | Multi-agent/fleet memory, given "Group" in the name — check if it already tests cross-agent memory sharing. (The old `suites/multi_agent_transfer` Track B suite this would have overlapped with was removed 2026-08-04 — see "Cross-repo context" below.) |
| LoCoMo | ⏳ queued — **priority 1** | `suites/recall_accuracy_locomo` (scaffolded, not populated) | Dataset needs populating — see `datasets/locomo/README.md`. **Product repo already publishes 77.6% LLM-judge accuracy / 96.6% token savings (run 2026-04-19, `caura-ai/caura` → `BENCHMARKS.md`) but with no baseline arm, no n, no judge model, no stats** — so the uncontrolled number exists and the *comparative* run still doesn't. See "Next action" item 1. |
| LongMemEval | ⏳ queued — **priority 1** | `suites/recall_accuracy_longmemeval` (scaffolded, not populated) | Dataset needs populating — see `datasets/longmemeval/README.md`. Same as LoCoMo: product repo publishes 72.5% accuracy / 98.2% token savings (2026-04-19), unbaselined. |

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
`all_results.json` summaries). Recomputed all three arms' aggregates directly
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
paper. All effects point the same direction as math and are considerably
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
versus ~$38 for gemini, which is why gemini went first. The account has been
topped up partway (**$48.40** balance / $107.13 key-limit headroom as of
2026-08-20, after the phys mem0 gemini run) — still not enough for either
Opus 5 or gpt-5.6-sol. The team reported (external update, not yet
reconciled into this file) that Opus 5 math had reached 28/40 papers on a
separate machine/environment not visible from this checkout — same "ran
elsewhere" gap as CL-Bench (item 4 below); needs pulling in before citing.
Next, in priority order:

1. **LoCoMo / LongMemEval** — now the biggest remaining gap, and the only
   priority-1 item. These are the recall-accuracy benchmarks this repo is
   actually built around, and they're still just scaffolded
   (`suites/recall_accuracy_locomo`, `suites/recall_accuracy_longmemeval`),
   never populated or run. Everything run so far (travel, math, phys) is
   external MemoryArena-Rotation work.

   **The MemClaw product repo already publishes its own numbers for both**
   (`caura-ai/caura`, `BENCHMARKS.md`, last run **2026-04-19**):
   LoCoMo **77.6%** / LongMemEval **72.5%** LLM-judge accuracy, plus token
   savings vs full context of **96.6%** / **98.2%**, and search latency
   23ms p50 / 27ms p95 warm. Checked 2026-08-10 — **this does not retire this
   item**, because those numbers are bare accuracy with, per the document
   itself, **no baseline or competitor arm, no stated sample size, no named
   judge or answering model, and no statistical test or per-question
   results**. (It asserts "MemClaw, Mem0, Zep land in a narrow band" without
   figures. The only paired bootstrap/sign-test in that repo covers two
   internal retrieval sub-benchmarks — `benchmark_rerank_locomo.py`,
   `benchmark_blend_locomo.py` — not the headline table.) That is exactly the
   raw-aggregate-without-a-control shape the method note below rejects.

   **So the job here is not to reproduce 77.6% — it's to produce the
   comparative, paired version** (memclaw / mem0 / full_context / no_memory
   on the same questions, bootstrap CI + McNemar), which is what made the
   MemoryArena results defensible and is the one thing the product numbers
   cannot support. Treat 77.6/72.5 as a **sanity-check target** for our own
   memclaw arm: landing far off it means our harness or seeding is wrong, not
   that the product regressed.

   Scoped 2026-08-09; it is more than a dataset download. Four things are
   needed:
   - **Dataset fetch + convert.** `scripts/fetch_locomo.py` is named in
     `datasets/locomo/README.md` but **was never written**. Both datasets need
     converting into the flat `conversation_*.jsonl` / `qa_*.jsonl` pair the
     harness expects.
   - **Baseline arms don't produce scoreable output.** In
     `runners/recall_accuracy.py`, only the `memclaw` condition calls
     `run_suite` (which writes `results/<run_id>.json` with per-question
     records). `full_context` and `no_memory` just `print()` an aggregate
     accuracy and keep nothing per-question — so the paired bootstrap/McNemar
     method used for every MemoryArena result **cannot be applied as the code
     stands**. Fix this before running anything, or the run produces a raw
     aggregate delta, which the method note below explicitly rejects as
     evidence.
   - **No mem0 arm exists here at all.** MemoryArena's headline comparison is
     now three-way; this harness only has memclaw / full_context / no_memory.
     A mem0 condition needs adding for the results to be comparable.
   - **One conversation per invocation.** `cli()` takes a single
     `--conversation-file` (default `conversation_001.jsonl`) with no
     cross-conversation aggregation, so a multi-conversation run needs a loop
     plus a combine step.
   Also note the judge here is **`claude-sonnet-5` via the Anthropic API**
   (`judges/llm_judge.py`, needs `ANTHROPIC_API_KEY`) — a different provider
   and key from the OpenRouter setup all MemoryArena work used.

   **Unresolved tension to settle while doing this — token efficiency.**
   `BENCHMARKS.md` claims **96.6% / 98.2% token savings vs full context**.
   Our travel measurement found the opposite direction: memclaw used **112k
   input tokens/group vs none's 104k (~1.07x *more*)**, and the travel `none`
   arm inlines all prior plans, so it is a full-context-style comparator. Both
   can be true — different tasks, different pipelines, and travel's memclaw
   prompts stayed large regardless — but **the two numbers should not
   circulate side by side unreconciled**. The `full_context` condition in
   `runners/recall_accuracy.py` is exactly the comparator that settles it, and
   it is one of the arms that currently keeps no per-question record, so
   fixing bullet 2 above also unblocks this.
2. **Shopping stays deferred but is now more worth doing** — two formal-reasoning
   domains discriminating at gpt-4.1 makes a third (different-shaped) task
   worthwhile, but it needs a multi-GB product DB, a JDK, spacy
   `en_core_web_lg`, and an extra upstream service (see table) — still a
   heavy, deliberate setup, not a quick add.
3. Investigate the abandoned `math_gpt5mini` partial run (`results/json/math_gpt5mini/`,
   2 papers done, memclaw only) found 2026-08-04 — figure out whether it's
   worth resuming/discarding, and who/what started it.
4. Pull over the CL-Bench quick_test results/logs from wherever that run
   actually happened (different machine/worktree, not this checkout) so
   they can be recorded here with real numbers instead of "ran elsewhere."
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

STATE-Bench is on hold pending an Azure OpenAI resource (see table above);
don't resume it until that's sorted.

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

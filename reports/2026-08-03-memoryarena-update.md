# MemoryArena benchmark update — MemClaw vs. no-memory

**Date:** 2026-08-03
**Scope:** MemoryArena-Rotation, travel + formal-reasoning (math) domains
**Agent model:** `openai/gpt-4o-mini` via OpenRouter (both arms, all runs)

---

## TL;DR

We now have MemClaw running end-to-end on two MemoryArena domains with a
matched no-memory control on each.

- **Travel: no effect.** MemClaw and no-memory are statistically
  indistinguishable. This one is settled — and the benchmark is too small to
  ever resolve an effect this size, so scaling the run up is not worth doing.
- **Math: consistent direction in MemClaw's favour, but not statistically
  significant.** Three independent metrics all lean the same way (p ≈
  0.14–0.25). This is underpowered, not absent — but it cannot be claimed as
  a win today.
- **Neither result is a MemClaw defect.** The controls scored the same, which
  means the adapter is working and the benchmark is simply hard at this model
  tier.
- **Please do not circulate "3x better on math."** See the caveat below — the
  raw numbers invite that reading and it is not supportable.

---

## Please read this before quoting a number

The math headline is `0.150` vs `0.050` paper passrate. That looks like a 3x
win. It is **6 papers versus 2 papers out of 40**, at **p = 0.22**, on a metric
that reduces each paper to a single noisy binary (see "how it's scored" below).

If that figure circulates as a result and then fails to replicate at a stronger
model, walking it back is expensive. The defensible statement today is:

> On MemoryArena's math domain, MemClaw led the no-memory baseline on all three
> scored metrics, but none of the differences reached statistical significance
> at the benchmark's full sample size.

---

## What was run

| domain | scale | arms | status |
|---|---|---|---|
| travel | 50 groups / 340 persons | memclaw, none | complete |
| math (formal reasoning) | 40 papers / 354 subtasks — **the full test split** | memclaw, none | complete |
| shopping | — | — | blocked, see below |

Both arms in each domain ran the **same items** with configs that are identical
apart from the memory system, so the comparisons are paired and controlled.

---

## Results

### Travel — no effect

| arm | groups | PS | SPS | SR |
|---|---|---|---|---|
| memclaw | 50 | 0.29% | 14.87% | 0.00% |
| none | 50 | 0.29% | 13.81% | 0.00% |

The +1.06pp SPS gap does not survive a paired test over the same 50 groups:

- 95% CI (bootstrap): **[−1.63, +3.76] pp** — spans zero
- permutation test: **p = 0.448**
- per-group wins: memclaw 24, none 21, tied 5 — a coin flip
- stdev of paired differences: 9.86pp, roughly 9x the effect

An earlier 13-group sample showed +1.72pp. At 50 groups it fell to +1.06pp.
**The gap shrank as n grew**, which is the signature of noise regressing, not
of a real effect emerging.

**Do not run the full 270 groups.** Detecting a 1.06pp effect at this variance
needs ~678 groups; the benchmark has 270. The smallest effect detectable at
n=270 is 1.68pp — larger than what we observed. The ~4–5 hours that run would
cost cannot produce a significant answer.

We also checked whether memory buys **token efficiency** instead, since the
no-memory arm stuffs all prior plans into context. It does not: 112k input
tokens/group for MemClaw vs 104k for no-memory — about 7% *more*, not less.
(Indicative rather than exact; the two 25-group subsets compared differ.)

**Why travel can't discriminate here:** SR is 0/50 for both arms and PS is
1/340 — literally the same single person passes in both. All the resolution
sits in SPS, a partial-credit score. gpt-4o-mini cannot do this task, so there
is no headroom for memory to matter.

### Math — consistent lead, not significant

| arm | paper passrate | avg progress score | avg memory length |
|---|---|---|---|
| memclaw | 0.150 (6/40) | 11.77% | 896 tok |
| none | 0.050 (2/40) | 9.40% | 0 tok |

The control's memory length of exactly 0 confirms it genuinely ran memory-free.

| metric | test | result | p |
|---|---|---|---|
| progress score (40 paired papers) | bootstrap + permutation | +2.37pp, 95% CI [−1.14, +6.40] | 0.247 |
| subtask correctness (354 subtasks) | McNemar exact — 19 vs 10 own-only | favours memclaw | 0.136 |
| paper passrate (40 papers) | McNemar exact — 5 vs 1 discordant | favours memclaw | 0.219 |

Per-paper outcomes: memclaw 9, none 7, **tied 24**.

**This is a different shape from travel.** Travel was a true null with the gap
shrinking as n grew. Math has three independent metrics agreeing in direction
at p ≈ 0.14–0.25. That is an underpowered signal, not an absent one — worth
pursuing, not worth announcing.

**How it's scored (important):** the benchmark defines a paper as "correct" by
whether its **final subtask** is right, not all of them. Nothing scores
all-correct — that's 0/40 for both arms. So `passrate` is "did the last answer
land", one binary per paper. It is arguably the *right* memory metric, since
the last subtask depends on the most accumulated context, but it has very
little resolution.

### Two follow-up diagnostics

**Supporting the effect:** MemClaw's advantage **grows with subtask position** —
+1.7pp over the first third of a paper's subtasks, +2.9pp over the middle,
+3.1pp over the last. That is the shape a real memory mechanism should produce,
since later subtasks have more accumulated context to draw on. An artifact
would not trend.

**Complicating it:** at **subtask 0, where memory is empty and there should be
no difference at all**, MemClaw still leads 4/40 vs 2/40. At n=40 that is well
inside noise, but it means part of the aggregate gap could be a baseline offset
rather than memory — MemClaw's prompt carries an empty `<memory_context>`
wrapper, so the two arms' prompts are not byte-identical even with nothing
stored. Treat the position trend as *weak supporting* evidence, not proof.

**One hypothesis tested and rejected:** we suspected the LLM judge was adding
noise, since it is configured at temperature 1.0. Re-judging 60 stored
(answer, ground-truth) pairs three times each produced **0/60 inconsistent
verdicts** at both temperature 1.0 and 0.0. The judge is stable; the variance
in these results is real task variance. No fix needed.

---

## More MemoryArena data will not settle this

Power analysis at the observed effect sizes:

| metric | needed for 80% power | available |
|---|---|---|
| math progress score | ~213 papers | 40 |
| math subtask McNemar | ~964 subtasks | 354 |
| travel SPS | ~678 groups | 270 |

`formal_reasoning_phys` is the only other formal-reasoning split and adds just
20 papers / 86 subtasks. Pooling reaches 440 subtasks against ~964 needed.

**Chasing significance by adding MemoryArena samples is not viable.** The
constraint is the benchmark's size, not our budget or patience.

---

## Harness work (valuable regardless of the scores)

MemClaw now has working MemoryArena adapters for travel and math, plus paired
no-memory controls and 4-way sharding (a 50-group travel config went from ~55
min sequential to ~7–8 min).

Seven real bugs found and fixed along the way. **Two of them meant no
no-memory baseline could be scored at all** — anyone else benchmarking on
MemoryArena would hit these:

1. `eval.py` crashed with `TypeError` on any no-memory run — `memory_context`
   is present-but-`None`, so the `''` default never applies and tiktoken
   rejects it. **Blocked all baseline scoring.**
2. Math had no no-memory code path whatsoever — the memory client 400s on
   `"none"`. Added a null client. **Blocked all baseline running.**
3. `eval.py` read UTF-8 result files with no encoding → crash on math symbols
   (Windows cp1252).
4. `run_math.py` swallowed every per-paper exception and then logged
   `COMPLETED`, so a run where all 40 papers failed looked like a clean pass
   that just wrote no results. This is exactly how bug 7 first presented.
5. Shards died mid-run on `UnicodeEncodeError` when harness output contained
   non-latin1 characters.
6. On resume runs, shards that did no work overwrote real token/cost data with
   zeros.
7. Travel's token/cost tracking silently reported zero for every
   OpenRouter-routed config (OpenRouter only returns usage when explicitly
   asked).

Also documented: the env server needs its own API key for math (it hosts the
judge), `auto_eval_after_run` does nothing (the call is commented out
upstream), and `main()` is invoked twice in the math runner.

---

## Recommendation / next step

**Re-run math at a stronger agent model.** gpt-4o-mini tops out at ~10%
progress score — a model that largely cannot solve the task cannot demonstrate
benefit from remembering. A larger effect needs far fewer samples than a small
one, so this is a better lever than more data.

Proposed: **`openai/gpt-5-mini`** ($0.25/$2.00 per M tokens, 400k context).
Verified it accepts the math harness's exact call shape, along with four other
candidates, so no code change is needed to swap models.

**Go/no-go criterion — pilot ~8 papers per arm first (~10 min):**

- If progress score lands in a discriminating **30–70%** range → run the full
  split both arms (~$2, ~45 min per arm) and re-test.
- If it stays near ~10% → the domain is too hard at any budget we'd spend, and
  MemoryArena stops being the right vehicle for this question.

**Deferred / blocked:**

- **Shopping** — needs a multi-GB product DB, a JDK, a spacy model, and a
  separate upstream service. Not worth the setup cost to add another
  gpt-4o-mini datapoint; revisit only if a stronger model makes the other
  domains discriminate.
- **mem0 third-party baseline** — no API key available.
- **STATE-Bench** — still blocked on an Azure OpenAI resource.

**Open question for the team:** if gpt-5-mini also comes back flat, is
MemoryArena the right benchmark for MemClaw's differentiators at all? Its
tasks measure end-task success, which memory only indirectly influences.
Track B suites (keystones, fleet transfer, contradiction convergence) may
exercise what MemClaw actually does better than any of these end-task
benchmarks can.

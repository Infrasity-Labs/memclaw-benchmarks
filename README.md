# memclaw-benchmarks

Benchmark suite for [MemClaw](https://memclaw.net), in the spirit of
[mem0ai/memory-benchmarks](https://github.com/mem0ai/memory-benchmarks) but
extended with suites for the things MemClaw does that single-agent memory
tools (mem0, Zep, Letta, Cognee) don't: **mandatory governance (keystones)**
and **shared fleet memory across agents**.

## Two tracks

**Track A — recall accuracy** (comparable to the rest of the field):
public long-term-memory QA datasets, LLM-judge scored, three conditions per
question (memclaw recall / full-context dump / no-memory blind).

| Suite | Dataset |
|---|---|
| `suites/recall_accuracy_locomo` | LOCOMO |
| `suites/recall_accuracy_longmemeval` | LongMemEval |

**Track B — MemClaw differentiators** (no existing public benchmark covers
these):

| Suite | What it measures |
|---|---|
| `suites/keystone_enforcement` | Does a mandatory keystone rule actually change agent behavior on trap tasks designed to violate it? |
| `suites/multi_agent_transfer` | Can Agent B answer using a fact only Agent A wrote, via shared fleet memory — vs. an isolated agent that can't? |
| `suites/trust_tier_access` | Do trust-1/2/3 read/write/delete permissions match the documented rules? (pass/fail security suite) |
| `suites/contradiction_convergence` | When Agent B corrects a stale fact Agent A wrote, does Agent C's later recall converge on the correction? |
| `suites/fleet_scale_compounding` | Does a late-joining agent inherit the fleet's accumulated knowledge, vs. starting from zero like a single-agent tool would? |

Track A is scored by an LLM judge (paraphrase-tolerant correctness, same
methodology mem0 uses). Track B suites 1 and 3 are pass/fail compliance
assertions, not judged similarity, since they're testing rule-following and
access control, not answer quality.

We deliberately don't wire up competitor SDKs (mem0/Zep/etc.) here — Track B
has no fair equivalent to compare against (those tools don't have a
governance layer or fleet-shared memory), and Track A is already comparable
via the same public datasets and methodology those tools' own benchmarks use.

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

Track A datasets need populating first — see `datasets/locomo/README.md` and
`datasets/longmemeval/README.md`. Track B datasets are already checked in
under `datasets/custom/` (small, hand-authored scenarios).

`suites/trust_tier_access` additionally needs three pre-provisioned agent
credentials at trust level 1/2/3 (trust is granted by an operator, not
self-assignable): set `MEMCLAW_TRUST{1,2,3}_AGENT_ID` and
`MEMCLAW_TRUST{1,2,3}_API_KEY`.

## Running

```bash
# Track A -- sanity-check on a handful of questions first
python suites/recall_accuracy_locomo/run.py --condition memclaw --limit 5
python suites/recall_accuracy_locomo/run.py --condition full_context --limit 5
python suites/recall_accuracy_locomo/run.py --condition no_memory --limit 5

# Track B
python suites/keystone_enforcement/run.py
python suites/multi_agent_transfer/run.py --fleet-id <your-fleet-id>
python suites/trust_tier_access/run.py
python suites/contradiction_convergence/run.py --fleet-id <your-fleet-id>
python suites/fleet_scale_compounding/run.py --fleet-id <your-fleet-id> --n-agents 4
```

Each run writes a JSON file to `results/` with per-item detail plus an
aggregate metric, so results are diffable across runs over time.

## Repo layout

```
datasets/       public dataset caches (locomo, longmemeval) + custom Track B scenarios
suites/         one dir per benchmark, each with a run.py entrypoint
runners/        shared harness + memclaw REST client
judges/         LLM-judge scoring (Track A) and pass/fail assertions (Track B governance/security)
results/        one JSON file per run
```

# Cost Model

What Chalksmith costs to run on Google Cloud, and which configuration choices in [GCP.md](GCP.md) are the ones that move the number. Infrastructure only — Vertex AI token spend is discussed in [Section 5](#5-where-cost-actually-grows) but not priced here.

Every figure below is a list price for `us-central1` (Tier 1) and is an estimate, not a quote. Rates change; recompute with the script in [Appendix A](#appendix-a-recomputing) rather than trusting a number that was true when this was written.

## 1. Assumptions

| Input | Value | Source |
| :--- | :--- | :--- |
| Traffic | 100–500 requests/day | Product estimate |
| Generations | ~20/day, ~120s of render each | Product estimate |
| Month | 30 days | |
| Production | Runs continuously | [GCP.md §2.3](GCP.md#23-database-initialization-and-v1-migration) |
| Staging | Stopped between sessions | [GCP.md §2.3](GCP.md#23-database-initialization-and-v1-migration) |

Cloud Run rates, per second:

| | Request-based | Instance-based |
| :--- | ---: | ---: |
| vCPU | $0.000024 | $0.000018 |
| Memory (GiB) | $0.0000025 | $0.000002 |
| Requests | $0.40 / million | none |
| Billed for | Time spent processing, starting, shutting down | The container's entire lifetime |

Always-free monthly allotment, aggregated per billing account: 180,000 vCPU-seconds, 360,000 GiB-seconds, 2 million requests. It is consumed once, not once per environment.

## 2. Production baseline

| Line | Monthly | Notes |
| :--- | ---: | :--- |
| Cloud SQL `db-f1-micro`, 24/7, 10 GB SSD | ~$10 | Runs continuously by definition |
| PITR write-ahead log archive | ~$1 | Scales with write volume, negligible here |
| Cloud Run, three services at `--min 0` | ~$0 | Inside the free allotment at this traffic |
| Cloud Scheduler keep-warm job | $0–$0.10 | One job every 3 minutes; first three jobs per billing account are free |
| GCS + Artifact Registry | ~$1–2 | Grows with retained image tags |
| **Total** | **~$12** | |

Five sixths of that is the database, and it cannot be reduced — the tier is already the smallest Cloud SQL sells. Staging adds only its 10 GB of storage as long as it stays stopped.

The practical consequence: **there is no infrastructure tuning left worth doing.** Effort spent shaving Cloud Run is effort spent on a line that already rounds to zero.

## 3. Cloud SQL

`ENTERPRISE` + `db-f1-micro` is the floor and not a preference:

- `db-f1-micro` (0.2 shared vCPU, 0.6 GB) is the smallest machine offered.
- It exists only in the Enterprise edition. Enterprise Plus starts at a 2 vCPU performance-optimized machine — roughly ten times the price — and rejects `db-f1-micro` outright.
- 10 GB is the minimum disk. HDD would save under a dollar a month and collapse IOPS at that size.
- `ZONAL` rather than regional HA: regional doubles the instance price.

What that buys, and what it does not: no SLA, and a zone outage is an outage. That is a deliberate trade at 100–500 requests a day, where the jump to a dedicated-core machine with regional HA costs roughly five times as much. Revisit when downtime costs more than the tier does, not before.

Google classifies shared-core tiers as low-cost test and development machines and recommends against production use. The current production choice is therefore a deliberate cost/reliability exception: monitor connection pressure, memory, latency, and restarts, then move to dedicated core before traffic or uptime requirements outgrow it.

Backups diverge by environment because their value does, not to save money. Staging is reproducible from a deploy, so its backups are pure waste. Production holds lessons a user paid Vertex AI tokens to generate; daily backups alone would put the recovery point up to 24 hours back, and the WAL archive that closes that gap costs about a dollar a month at this write volume. Enable PITR in production.

Stopping is the only real lever, and it only applies to staging: stopped, an instance bills storage alone — roughly a sixth of what it costs running.

## 4. Cloud Run

### 4.1 Which model is cheaper

**Request-based, by a wide margin.** Instance-based buys a ~25% lower per-vCPU-second rate in exchange for paying through idle time, so the crossover sits near **75% utilization** — it only wins if a container spends more than three quarters of its lifetime actively serving. Google's own guidance says the same in words: request-based for "sporadic, bursty or spiky" traffic, instance-based for "steady, slowly varying" traffic.

Measured against this workload:

| | Active vCPU-s | Active GiB-s | Requests | Monthly |
| :--- | ---: | ---: | ---: | ---: |
| web + api | 9,000 | 6,750 | 15,000 | |
| renderer (600 renders × 120s) | 144,000 | 144,000 | — | |
| **Total** | **153,000** | **150,750** | **15,000** | **$0** |

All three fit inside the free allotment; even ignoring the free tier entirely, the same usage prices at $4.05/month. Utilization is on the order of 1% — two orders of magnitude below the crossover. `deploy.sh` passes `--cpu-throttling` explicitly so a prior service configuration cannot silently carry instance-based billing into the next revision.

### 4.2 What "lifetime" means under instance-based

The common misreading is that a service busy from 08:00–10:00 bills two hours. It does not. Instance-based bills the container's lifetime, and Cloud Run holds an idle container for roughly fifteen minutes before reclaiming it. So the peak itself bills 2.25 hours, and every isolated off-peak request drags about fifteen minutes of billed idle behind it — **900 seconds charged for 0.3 seconds of work.**

Billed hours per day, for a 2-hour morning peak plus scattered off-peak traffic:

| Off-peak traffic | Gap between requests | Alive/day | web + api monthly |
| :--- | ---: | ---: | ---: |
| None | — | 2.2h | $5.52 |
| 1–2 per day | 7h | 2.8h | $7.62 |
| 1 per hour | 60 min | 5.8h | $20.26 |
| 2 per hour | 30 min | 9.2h | $35.00 |
| 1 per 15 min | 15 min | 16.2h | $64.48 |
| Denser | <15 min | 16.2h | $64.48 |

Two regimes, split by the idle window. Above it, cost rises linearly with the number of isolated requests. Below it, the container never scales down at all and a lightly scattered afternoon bills exactly the same as a saturated one — which is why the last two rows are identical.

At the stated 500 requests/day, with 400 in the peak and 100 spread across the remaining 14 hours, gaps average about 8 minutes. That lands in the saturated regime: 16.2 hours a day, ~$64/month for web and api, versus ~$0 under request-based.

The deeper objection is not the number. Fifteen minutes is observed behavior, not a documented guarantee — it can change, and longer means more expensive. Instance-based makes the bill a function of Google's scale-down heuristic; request-based makes it a function of traffic.

### 4.3 The one reason to switch anyway

Request-based billing throttles CPU once the response is sent, so work continuing after a response stalls. Generation currently holds the request open for its full duration, so it is unaffected. Moving generation to a background task that returns early would require always-allocated CPU regardless of price — a correctness requirement, not a cost decision.

### 4.4 Instance sizes and `--min`

CPU and memory are already at their practical floors and shrinking them saves nothing: billing is per vCPU-second, so halving a service's CPU roughly doubles how long each request holds it. Dropping the renderer below 2 vCPU only makes each Manim job twice as long against a 900s ceiling.

`--min` is a genuine choice, and the answer is **0, in production too.** A service at `--min 0` is still continuously available; it is the container that scales to zero, and the first request after an idle gap pays a few seconds of cold start. Keeping containers resident costs:

| Kept warm 24/7 | vCPU-s/month | GiB-s/month | Monthly |
| :--- | ---: | ---: | ---: |
| `--min 0` everywhere | 0 | 0 | $0 |
| web only | 2,592,000 | 1,296,000 | $45.29 |
| web + api | 5,184,000 | 3,888,000 | $97.13 |
| all three | 10,368,000 | 9,072,000 | $200.81 |

Note that this is the same arithmetic as instance-based billing: a resident minimum instance bills at the always-allocated rate whichever model the service uses.

At this traffic the containers stay warm through an active period anyway, since gaps average around a minute and the idle window is minutes long. Only the first visitor after a genuinely quiet stretch waits. Spend the $45 if cold starts prove visible in practice, and then only on `chalksmith-web`, where the delay is a blank page rather than a spinner.

`--max` is a cap, not a saving. The API is held at 2 because five instances × SQLAlchemy's default pool would demand more connections than `db-f1-micro` grants; one instance at concurrency 8 already covers this traffic, and the second exists for rolling deploys.

## 5. Where cost actually grows

Infrastructure is flat at this scale. Three things are not:

1. **Vertex AI generation**, billed per token, will overtake the entire $12 baseline well before the infrastructure does. It is the only line that scales with product success.
2. **Render volume.** Under request-based billing the renderer already consumes 85% of the free CPU allotment at 20 generations/day. The allotment runs out at roughly **24 generations/day**; past that each render costs about **$0.006**, which stays negligible for a long time but is no longer zero.
3. **Build and image storage.** Every deploy pushes images tagged with a git SHA and uploads source archives for two Cloud Build submissions. `deploy.sh` applies retention policies to both Artifact Registry and the shared Cloud Build source bucket so deploy frequency does not grow storage indefinitely.

The deploy template also exposes `LLM_MAX_OUTPUT_TOKENS` and `MAX_SOURCE_CHARACTERS`. These are the direct worst-case output and source-input guardrails; reduce them only after measuring real generated lessons, because values that are too small trade lower token spend for truncated code or incomplete source context. The source default is 200,000 characters: roughly 50,000 tokens for typical English text (about $0.075 of Gemini 3.6 Flash input) and up to about 200,000 tokens or $0.30 for dense CJK text. Raising it further adds latency and makes the shared provider configuration more likely to exceed a 128K-token context window.

Gemini response streaming does not change token prices: the API aggregates the same model output, logs usage once after completion, and never logs individual chunks. Streaming progress and ten-second fallback heartbeats add only negligible SSE bytes; retries remain explicit so an interrupted response is not silently regenerated and billed twice.

## Appendix A: Recomputing

```python
CPU_REQ, MEM_REQ, REQ = 0.000024, 0.0000025, 0.40/1_000_000   # request-based
CPU_INS, MEM_INS      = 0.000018, 0.000002                    # instance-based / min-instances
FREE_CPU, FREE_MEM, FREE_REQ = 180_000, 360_000, 2_000_000
IDLE_MIN, DAYS = 15, 30            # observed scale-to-zero delay; days per month

def request_based(work, requests):
    """work: [(vcpu, gib, active_seconds_per_month)]"""
    cpu = sum(v*s for v, _, s in work); mem = sum(g*s for _, g, s in work)
    return (max(0, cpu-FREE_CPU)*CPU_REQ + max(0, mem-FREE_MEM)*MEM_REQ
            + max(0, requests-FREE_REQ)*REQ)

def instance_based(services, hours_alive_per_day):
    """services: [(vcpu, gib)] all sharing one alive-time profile"""
    s = hours_alive_per_day * 3600 * DAYS
    cpu = sum(v*s for v, _ in services); mem = sum(g*s for _, g in services)
    return max(0, cpu-FREE_CPU)*CPU_INS + max(0, mem-FREE_MEM)*MEM_INS

def alive_hours(peak_h, offpeak_h, offpeak_per_hour):
    """Billed alive time per day, given the idle window."""
    if offpeak_per_hour <= 0:
        return peak_h + IDLE_MIN/60
    if 60/offpeak_per_hour <= IDLE_MIN:        # never scales down
        return peak_h + offpeak_h + IDLE_MIN/60
    return peak_h + IDLE_MIN/60 + offpeak_per_hour*offpeak_h*IDLE_MIN/60

# Current production shape:
print(request_based([(1, 0.5, 4500), (1, 1.0, 4500), (2, 2.0, 72000)], 15_000))   # ~0.0
print(instance_based([(1, 0.5), (1, 1.0)], alive_hours(2, 14, 7)))                # ~64.5
```

## References

- [Cloud Run pricing](https://cloud.google.com/run/pricing)
- [Cloud Run billing settings](https://cloud.google.com/run/docs/configuring/billing-settings)
- [Best practices for cost-optimized Cloud Run services](https://cloud.google.com/run/docs/tips/services-cost-optimization)
- [Cloud SQL pricing](https://cloud.google.com/sql/pricing)
- [Cloud SQL editions overview](https://cloud.google.com/sql/docs/postgres/editions-intro)
- [Cloud Storage pricing](https://cloud.google.com/storage/pricing)
- [Artifact Registry pricing](https://cloud.google.com/artifact-registry/pricing)

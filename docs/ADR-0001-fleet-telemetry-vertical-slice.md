# ADR-0001: Fleet telemetry vertical slice (50 vehicles, 1 Hz)

**Status:** Accepted  
**Context:** Assignment slice for ~50 autonomous vehicles emitting JSON telemetry about once per second, with concurrent writes, zone entry accounting, fault handling, and a small live dashboard.

---

## 1) Decisions that mattered most (and why)

### A. PostgreSQL + row-level locking on the hot paths

We chose **PostgreSQL** over SQLite because the spec explicitly calls out **concurrent bursts** (many vehicles entering the same zone in the same second, plus concurrent telemetry). SQLite’s single-writer model becomes a tail-latency bottleneck under overlapping writers. Postgres gives **row-level locks** (`SELECT … FOR UPDATE`) so we can:

- increment `zone_entry_counts` without lost updates, and  
- serialize **per-vehicle** transitions (telemetry + fault handling) predictably.

Alembic migrations use a **sync** driver (`psycopg2-binary`) while the API uses **async** (`asyncpg`)—a common split that keeps migrations boring and runtime concurrent.

### B. “Anomaly” = deterministic ingest-time rules (not ML)

“Real-time anomaly detection” is implemented as **cheap, explainable predicates** evaluated during `POST /telemetry` (see `app/services/anomaly_detection.py`), e.g. non-empty `error_codes`, `fault` status, critical low battery, inconsistent idle/speed, and a bounded-window rapid battery drop vs the last stored snapshot.

**Why:** sub-second ML pipelines are out of scope for a 5–6 hour slice; deterministic rules produce **auditable** rows in `anomalies` and match ops workflows (“why did this fire?”).

### C. Dashboard transport = **short polling** (not WebSockets)

The UI polls `/vehicles`, `/zones/counts`, and `/fleet/state` on a **2.5s** cadence.

**Why:** at ~50 entities, polling is simpler to deploy through proxies and corporate networks, avoids connection fan-out and auth complexity, and is “live enough” for warehouse supervision. The trade-off is added read QPS and ~1–2s staleness vs push.

---

## 2) Spec ambiguity + explicit assumptions

- **Missions lifecycle** was not fully specified. We assumed missions are **explicitly started** via `POST /vehicles/{id}/missions` and that **at most one active mission** exists per vehicle (partial unique index).
- **Idempotency / dedupe keys** for telemetry retries were not required; we did **not** implement idempotency keys.
- **AuthN/Z** was out of scope: endpoints are open on the local dev network.
- **Zone geometry** is intentionally absent; clients populate `zone_entered` only on boundary crossings.
- **Fault via telemetry vs fault via API:** both paths share the same **“transition into fault”** semantics for mission cancellation + maintenance creation to avoid split-brain behavior.

---

## 3) If scale grew “significantly” — what would change?

Define **significantly** as roughly **≥500–1,000 vehicles**, **≥500–1,000 sustained writes/sec**, multi-region fleets, or strict **sub-second** global dashboards.

Likely changes:

- **Ingest path:** move to an append-only event log (Kafka/NATS/Pulsar) + stream processors; API becomes a thin edge or disappears for direct device writes.
- **Counters / aggregates:** Redis/HyperLogLog or CQRS materialized views; zone counters may become **sharded** or **approximate** depending on accuracy requirements.
- **Reads:** dedicated read replicas, caching layers, and/or **SSE/WebSocket** fan-out with snapshot+delta protocols.
- **Anomaly detection:** online rules engine + optional model scoring in a separate service with backpressure and feature stores.

---

## 4) Deliberately left out (and why)

- **WebSockets/SSE**, auth, RBAC, multi-tenancy, retention policies, and on-call paging integrations.
- **Rich geospatial modeling** (zones as polygons) and map visualization.
- **Load testing harness** as a committed artifact (timeboxed); the design is intended to be stress-tested before production hardening.

These are valuable, but they were traded for a **reviewable vertical slice** with clear concurrency and data-model boundaries.

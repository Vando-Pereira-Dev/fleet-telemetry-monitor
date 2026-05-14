# AI interaction log

This file documents how AI assistance was used while building this repository (per assignment requirements). Prompts are paraphrased where needed for clarity; outputs are summarized, not full transcripts.

---

## Session timeline

### 1) Initial assignment + working agreement

**Prompt (summary):** Build the full fleet telemetry monitoring task (FastAPI/Django, persistence, anomalies, zone counters with concurrency guarantees, fault atomicity, REST queries, React TS dashboard, ADR, AI log). Work incrementally: analyze first, then implement step-by-step with **stop after each step**; suggest **professional short commit messages**; produce senior-quality results.

**AI output (summary):** Produced a phased technical plan (Postgres vs SQLite, FastAPI choice, locking strategy, anomaly definitions, polling vs websockets, data model sketch) and a commit map (Steps A–H). Did not implement code in that first step.

**Corrections / steering:** User asked for incremental delivery; plan explicitly separated “analysis only” vs later implementation steps.

---

### 2) “Briefly inform…” (meta)

**Prompt (summary):** Briefly inform the user about the task result and perform follow-ups if needed.

**AI output (summary):** Confirmed Step B scaffold outcome and suggested a commit message; invited “continue” for Step C.

---

### 3) Continue → Step C (database)

**Prompt:** `continue`

**AI output (summary):** Added SQLAlchemy models, Alembic migration + seed (50 vehicles, 20 zones), `/ready` DB check, `psycopg2-binary` for migrations, README migration instructions.

**Corrections / manual verification:** Docker was not available in the automation environment; migrations were validated via `alembic history` and imports rather than a live `upgrade` run.

---

### 4) Continue → Step D (telemetry ingest)

**Prompt:** `continue`

**AI output (summary):** Implemented `POST /telemetry`, transactional ingest, `FOR UPDATE` ordering (vehicle then zone), deterministic anomaly detection module, Pydantic validation (including `timestamp` alias).

**Corrections:** None significant from the user; implementation followed the earlier plan.

---

### 5) Continue → Step E (read APIs)

**Prompt:** `continue`

**AI output (summary):** Added `GET /zones/counts`, `GET /fleet/state`, `GET /anomalies` with filters and README updates.

**Corrections:** None reported.

---

### 6) Continue → Step F (fault + missions)

**Prompt:** `continue`

**AI output (summary):** Added shared fault workflow (cancel active mission + maintenance record), `POST /vehicles/{id}/status`, `POST /vehicles/{id}/missions`, and telemetry integration for first transition into `fault`.

**Corrections / fix during implementation:** A `NameError` occurred for `VehicleStatusUpdate` return annotation in the Pydantic model; fixed by adding `from __future__ import annotations` in `backend/app/schemas/vehicles.py`.

---

### 7) Continue → Step G (dashboard)

**Prompt:** `continue`

**AI output (summary):** Added `GET /vehicles` snapshot SQL (`LATERAL` join for latest anomaly), CORS for Vite dev ports, React+TS Vite app with polling UI, `frontend/.env.example`, README dashboard section. Ran `npm install` + `npm run build` successfully.

**Corrections / environment notes:** Earlier shell friction on Windows (`&&` vs `;`) was handled by adjusting commands to PowerShell-friendly separators.

---

### 8) Brief status (meta)

**Prompt (summary):** Briefly inform the user about Step G completion.

**AI output (summary):** Summarized deliverables, noted optional `npm audit` follow-up, suggested commit message, invited continue for Step H.

---

### 9) Continue → Step H (this step)

**Prompt:** `continue`

**AI output (summary):** Added this `AI_INTERACTION_LOG.md`, `docs/ADR-0001-fleet-telemetry-vertical-slice.md`, and README documentation links/polish.

---

## Reflection (3–5 bullets)

- **What the AI was good at:** turning an ambiguous large spec into an incremental engineering plan; boilerplate for FastAPI/SQLAlchemy/Alembic/Vite; concurrency-minded patterns (`FOR UPDATE`, partial unique index) and keeping changes scoped per step.
- **Where it failed / risked slipping:** small Python typing footguns (Pydantic forward references) and environment assumptions (POSIX shell vs PowerShell; Docker availability) required a quick correction or alternate verification path.
- **What I double-checked manually:** migration/DDL alignment with models, route registration order (`GET /vehicles` vs parameterized routes), and that the dashboard build actually succeeds (`tsc && vite build`).
- **What I would do differently next time:** add a tiny `docker compose` smoke step earlier (or document “no Docker in CI sandbox”) to reduce ambiguity about whether migrations ran against a live DB.

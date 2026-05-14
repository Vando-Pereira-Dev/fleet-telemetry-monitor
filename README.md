# Fleet Telemetry Monitor

Vertical slice: ingest telemetry from a fleet of industrial vehicles, detect anomalies, track zone entries, and expose fleet state via REST. A small React dashboard consumes those APIs.

## Prerequisites

- **Python 3.11+**
- **Docker** (for PostgreSQL during development)

## Backend setup

1. **Start PostgreSQL**

   ```bash
   docker compose up -d
   ```

   Wait until the container is healthy (`docker compose ps`).

2. **Configure environment (optional)**

   From the repo root, you can copy the example file into `backend/.env` if you need non-default DB credentials:

   ```bash
   copy .env.example backend\.env
   ```

   On Linux or macOS:

   ```bash
   cp .env.example backend/.env
   ```

   Default URL matches `docker-compose.yml` (`fleet` / `fleet` / `fleet_telemetry` on port `5432`).

3. **Install Python dependencies**

   ```bash
   cd backend
   python -m venv .venv
   ```

   Activate the venv:

   - Windows (PowerShell): `.\.venv\Scripts\Activate.ps1`
   - Linux/macOS: `source .venv/bin/activate`

   Then:

   ```bash
   pip install -r requirements.txt
   ```

4. **Apply database migrations**

   From the `backend` directory (with venv activated and PostgreSQL running):

   ```bash
   alembic upgrade head
   ```

   This creates all tables and seeds **50** vehicles (`v-1` … `v-50`, status `idle`) and **20** zone rows (`entry_count = 0`). Zone IDs match `app/constants.py` (`ZONES`).

5. **Run the API**

   From the `backend` directory (with venv activated):

   ```bash
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

6. **Verify**

   - Health: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health) → `{"status":"ok"}`
   - Database readiness: [http://127.0.0.1:8000/ready](http://127.0.0.1:8000/ready) → `{"status":"ready","database":"connected"}` (returns **503** if Postgres is down or URL is wrong)
   - OpenAPI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### Ingest telemetry (`POST /telemetry`)

With the API running and migrations applied, post a sample event (JSON uses **`timestamp`** for event time):

```bash
curl -s -X POST http://127.0.0.1:8000/telemetry -H "Content-Type: application/json" -d "{\"vehicle_id\":\"v-1\",\"timestamp\":\"2026-05-14T12:00:00Z\",\"lat\":37.41,\"lon\":-122.08,\"battery_pct\":78,\"speed_mps\":1.2,\"status\":\"moving\",\"error_codes\":[],\"zone_entered\":null}"
```

A **201** response includes `telemetry_event_id` and how many `anomalies` rows were created for that event. Rules live in `app/services/anomaly_detection.py` and will be summarized in the ADR.

### Read APIs

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/zones/counts` | Per-zone `entry_count` in `ZONES` order |
| `GET` | `/fleet/state` | Fleet-wide counts by `current_status` plus `total` vehicles |
| `GET` | `/anomalies` | Recent anomalies; optional `vehicle_id`, `from_ts`, `to_ts` (ISO-8601), `limit` (default 200, max 2000) |
| `POST` | `/vehicles/{vehicle_id}/status` | Status change; transitioning **to `fault`** cancels the active mission (if any) and creates a **maintenance** row (requires `maintenance_reason`) |
| `POST` | `/vehicles/{vehicle_id}/missions` | Start an **active** mission when none exists (**409** if one is already active) |

Examples:

```text
GET http://127.0.0.1:8000/zones/counts
GET http://127.0.0.1:8000/fleet/state
GET http://127.0.0.1:8000/anomalies?vehicle_id=v-1&from_ts=2026-05-01T00:00:00Z&to_ts=2026-05-31T23:59:59Z
POST http://127.0.0.1:8000/vehicles/v-12/status
POST http://127.0.0.1:8000/vehicles/v-12/missions
```

`POST /vehicles/{id}/status` body (fault example): `{"status":"fault","maintenance_reason":"Motor controller overcurrent"}`. A first-time **`fault`** via `POST /telemetry` runs the same cancel-and-maintenance workflow (reason from `error_codes` or a default string), but **only on the transition into fault** (no duplicate maintenance while already fault).

## Repository layout

| Path | Purpose |
|------|---------|
| `backend/` | FastAPI application |
| `backend/alembic/` | Alembic migrations (`001_initial` = schema + seed) |
| `backend/app/constants.py` | `ZONES`, fleet size, allowed status strings |
| `backend/app/db/models.py` | SQLAlchemy models |
| `backend/app/api/routes/telemetry.py` | `POST /telemetry` |
| `backend/app/services/telemetry_ingest.py` | Transactional ingest + row locks |
| `backend/app/api/routes/anomalies.py` | `GET /anomalies` |
| `backend/app/api/routes/fleet.py` | `GET /fleet/state` |
| `backend/app/api/routes/zones.py` | `GET /zones/counts` |
| `backend/app/api/routes/vehicles.py` | `POST /vehicles/.../status`, `POST /vehicles/.../missions` |
| `backend/app/services/fleet_commands.py` | Fault transition + mission start (row locks) |
| `docker-compose.yml` | Local PostgreSQL 16 |
| `.env.example` | Sample `DATABASE_URL` |

## License

Proprietary / assignment — adjust as needed.

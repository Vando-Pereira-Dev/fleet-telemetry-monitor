# Fleet Telemetry Monitor

Vertical slice: ingest telemetry from a fleet of industrial vehicles, detect anomalies, track zone entries, and expose fleet state via REST. A small React dashboard consumes those APIs.

## Prerequisites

- **Python 3.11+**
- **Docker** (for PostgreSQL during development)

## Quick start (backend only — this step)

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

4. **Run the API**

   From the `backend` directory (with venv activated):

   ```bash
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Verify**

   - Health: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health) → `{"status":"ok"}`
   - OpenAPI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

The database is not wired into the app until the next implementation step; the API runs without a successful DB connection for now.

## Repository layout

| Path | Purpose |
|------|---------|
| `backend/` | FastAPI application |
| `docker-compose.yml` | Local PostgreSQL 16 |
| `.env.example` | Sample `DATABASE_URL` |

## License

Proprietary / assignment — adjust as needed.

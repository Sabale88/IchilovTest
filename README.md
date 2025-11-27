# Patient Monitoring System

Monitors hospitalized patients and surfaces those whose latest lab test exceeds a configurable hour threshold (default 48 h). Includes a FastAPI backend, PostgreSQL database, and React + Vite frontend.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [PostgreSQL Setup](#postgresql-setup)
4. [Loading CSV Data](#loading-csv-data)
5. [Running the Application](#running-the-application)
6. [API Endpoints](#api-endpoints)
7. [Running Tests](#running-tests)
8. [Project Structure](#project-structure)
9. [Troubleshooting](#troubleshooting)
10. [Production Considerations](#production-considerations)

## Prerequisites
- **Python 3.10+**
- **Node.js 18+ / npm 9+**
- **PostgreSQL 13+** (local or remote)
- **Git**

## Installation
```bash
git clone <repo-url>
cd IchilovTask

python -m venv venv
source venv/bin/activate         # Windows: venv\Scripts\activate
pip install -r backend/requirements.txt

cp backend/.env.example backend/.env   # Windows: copy backend\.env.example backend\.env
```
Edit `backend/.env` and set:
```
DATABASE_URL=postgresql://USER:PASSWORD@localhost:5432/ichilov
```

## PostgreSQL Setup
1. Install PostgreSQL (https://www.postgresql.org/download/).
2. Create a database (e.g. `ichilov`) and user with full privileges:
   ```sql
   CREATE DATABASE ichilov;
   CREATE USER ichilov_user WITH ENCRYPTED PASSWORD 'secret';
   GRANT ALL PRIVILEGES ON DATABASE ichilov TO ichilov_user;
   ```
3. Update `DATABASE_URL` accordingly, e.g. `postgresql://ichilov_user:secret@localhost:5432/ichilov`.

## Loading CSV Data
> Run from project root with your virtual environment activated.
```bash
python -m backend.app.db.bootstrap_db      # loads csvFiles/ into base tables
python -m backend.app.db.snapshot_builder  # builds monitoring + detail snapshots
```
Re-run the snapshot builder whenever CSV data changes.

## Running the Application
### Backend
```bash
uvicorn backend.app.main:app --reload --port 8000
```
- API root: http://localhost:8000
- Docs: http://localhost:8000/docs

### Frontend
```bash
cd frontend
npm install
npm run dev
```
- Frontend: http://localhost:3000 (Vite proxies `/api` → backend)

Keep backend and frontend in separate terminals.

## API Endpoints
- `GET /api/health` – health check.
- `GET /api/patients/monitoring` – monitoring list; accepts `hours_threshold`, `department`, `page`, `limit`.
- `GET /api/patients/{patient_id}` – patient detail snapshot.

## Running Tests
```bash
source venv/bin/activate              # Windows: venv\Scripts\activate
pip install -r backend/requirements.txt

python -m pytest backend/tests                 # all tests
python -m pytest backend/tests/unit            # unit only
python -m pytest backend/tests/integration     # integration only
python -m pytest backend/tests -v              # verbose
python -m pytest backend/tests --cov=backend.app --cov-report=html
```
Always prefer `python -m pytest` to ensure the correct interpreter.

## Project Structure
```
backend/         FastAPI app, services, snapshot builders
frontend/        React + Vite client
csvFiles/        Source CSV data
README.md        You are here
HIGH_LEVEL_DESIGN.md  Architecture overview
```

## Troubleshooting
- **`pytest` not found**: activate `venv` and run `python -m pytest`.
- **DB connection errors**: confirm PostgreSQL is running and `DATABASE_URL` is correct.
- **Empty dashboard**: rerun `python -m backend.app.db.snapshot_builder` to refresh snapshots.
- **Port conflicts**: change backend `--port` or Vite dev port via env vars.

## Production Considerations
1. **Schema changes in source systems**  
   - ✅ Current state: CSV loader assumes the stable schema shipped with the task.  
   - 🔜 Next steps: add schema validation, versioning metadata, and a mapping layer (e.g. JSON fields or adapters) so new columns can be ingested without breaking snapshots.

2. **Frequent updates (every few seconds)**  
   - ✅ Current state: snapshots can be regenerated on demand to refresh the monitoring payloads.  
   - 🔜 Next steps: automate ingestion via a streaming/queue pipeline, schedule snapshot jobs (Celery/cron), and expose job health metrics so the UI always serves fresh cached data.

3. **Performance at hospital scale**  
   - ✅ Current state: PostgreSQL stores normalized tables plus precomputed JSONB snapshots; the frontend paginates and filters client-side.  
   - 🔜 Next steps: introduce incremental snapshot updates, database indexes/partitioning tuned for high volumes, server-side pagination when needed, and frontend optimizations (virtualized tables, memoized filters) for tens of thousands of rows.

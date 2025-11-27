# High-Level Design: Hospital Patient Monitoring System

## 1. System Overview

### 1.1 Purpose
A web application that monitors hospitalized patients and identifies those who have been admitted for more than 48 hours without any new laboratory tests being performed.

### 1.2 Data Sources
- **Patient Management System (PMS)**: Provides patient information and admission data
- **Laboratory Information System (LIS)**: Provides lab test orders and results
- **Data Format**: CSV files stored in S3 buckets (sync every few seconds)
- **Note**: S3 reading/processing is out of scope for this task

## 2. Architecture Overview

### 2.1 High-Level Architecture

```
┌─────────────────┐     ┌─────────────────┐
│   S3 Buckets    │     │   S3 Buckets    │
│   (PMS Data)    │     │   (LIS Data)    │
└─────────────────┘     └─────────────────┘
         │                       │
         │  (CSV Files)          │
         │                       │
         └───────────┬───────────┘
                     │
         ┌───────────▼───────────┐
         │   Data Loading Layer  │
         │   (Manual/ETL Process)│
         └───────────┬───────────┘
                     │
         ┌───────────▼───────────┐
         │    Database Layer     │
         │     (PostgreSQL)      │
         └───────────┬───────────┘
                     │
         ┌───────────▼───────────┐
         │    Backend API        │
         │ (FastAPI REST layer)  │
         └───────────┬───────────┘
                     │
         ┌───────────▼───────────┐
         │       Frontend        │
         │ (React + TypeScript)  │
         └───────────────────────┘
```
- **Data ingestion**: manual CLI scripts load CSVs located in `csvFiles/` into PostgreSQL. No live S3 integration today.
- **Snapshots**: `patient_monitoring_snapshots` and `patient_detail_snapshots` store precomputed JSON payloads for fast reads.
- **Backend**: FastAPI + SQLAlchemy expose `/patients/monitoring` and `/patients/{id}`, serving data from the latest snapshots (regenerating on cache miss).
- **Frontend**: React + TypeScript (MUI) fetch all monitoring pages once, then filter/sort client‑side. Alert chips highlight patients with overdue labs.

## 3. Data Model (Implemented)
- `patients`, `admissions`, `lab_tests`, `lab_results`: normalized clinical data imported from CSVs.
- Snapshot tables:
  - `patient_monitoring_snapshots(payload JSONB)` – list view, includes computed durations plus `needs_alert`.
  - `patient_detail_snapshots(payload JSONB)` – per‑patient detail (latest result per test + chart series).

### 3.3 Key Design Decisions
1. **Separate date/time fields** keep CSV fidelity while allowing precise datetime calculations in Python.
2. **Indexes on patient/department/timestamps** ensure snapshot queries stay sub‑second even with thousands of rows.
3. **Soft deletes + audit fields** (`deleted_at`, `created_at`, `updated_at`) let us reload data safely and trace changes.

## 4. Key Flows
1. **Bootstrap**  
   `python -m backend.app.db.bootstrap_db` truncates and reloads all base tables from CSVs.  
   `python -m backend.app.db.snapshot_builder` runs business rules:
   - keep only active admissions (no release or within 2‑hour grace).
   - compute hours since admission and last test; mark `needs_alert` when `>= threshold`.  
   - persist monitoring/detail payloads for the API.

2. **Backend Requests**  
   - `/patients/monitoring`: returns latest snapshot, supports department filter + pagination, normalizes `needs_alert` for old payloads.  
   - `/patients/{id}`: fetches detail snapshot, regenerating if missing.

3. **Frontend Experience**  
   - Loads all monitoring rows once (pages of 1000) using the 48 h snapshot.  
   - Provides client filters (department, age bin, physician, last test) and adjustable alert threshold.  
   - Displays `N patients - M alerts shown / K total` to reflect filters.  
   - Table rows link to `/patient/:id` detail view with the cached chart data.

### 4.1 Alert Selection Pseudocode
```
for admission in active_admissions:
    hours_admitted = now - admission_datetime
    if hours_admitted < threshold:
        continue
    last_test = latest_test_for_patient(admission.patient_id)
    hours_since_test = now - last_test.timestamp if last_test else None
    needs_alert = hours_since_test is None or hours_since_test >= threshold
    build monitoring entry with durations + needs_alert
    build detail payload using all tests for charts
```

## 5. Technology Stack
- **Backend**: Python 3.10, FastAPI, SQLAlchemy, Uvicorn.  
- **Database**: PostgreSQL; snapshots stored as JSONB.  
- **Frontend**: React 18, TypeScript, Vite, Material‑UI, Axios.  
- **Tooling**: pytest for backend tests, npm scripts for frontend, bash/PowerShell wrappers for setup.

## 6. API Design
- `GET /api/health` – basic liveness check.
- `GET /api/patients/monitoring` – returns latest snapshot, query params: `hours_threshold`, `department`, `page`, `limit`. Always normalizes payload to include `needs_alert`.
- `GET /api/patients/{patient_id}` – serves detail snapshot; regenerates if absent.

## 7. Frontend Design
- **Dashboard**: filters (department, hours threshold, age bins, physician, last test) + summary chip row + sortable/paginated table. Alerts indicated via colored chips and aggregate text (`patients - alerts shown / total`).
- **Patient Detail View**: header card (demographics), admission summary, latest-results table, chart series rendered from cached snapshot data.

## 8. Deployment & Ops (Dev Scope)
- Runs locally: PostgreSQL + FastAPI (`uvicorn`) + Vite dev server.  
- No containerization or cloud services included yet; future prod deployment would package backend/frontend separately and schedule snapshot jobs.

## 9. Data Flow
```
CSV files → bootstrap_db → core tables → snapshot_builder → snapshot tables
Frontend → FastAPI → snapshot table payload → React state / charts
```

## 10. Testing Strategy
- `pytest backend/tests` covers snapshot helpers, DB utils, and API contracts.  
- Frontend relies on manual verification today; Jest/RTL can be added later for component tests.  
- Integration tests hit the FastAPI endpoints with seeded SQLite/PostgreSQL fixtures.

## 11. Monitoring & Logging
- Structured stdout logging from FastAPI + snapshot jobs.  
- Health endpoint for liveness; extend with metrics (Prometheus) if deployed.  
- Future: add APM (Sentry/New Relic) and DB monitoring once running in production.

## 12. Future Considerations
- Automate CSV ingestion (S3 watcher or message queue).  
- Move snapshot generation to a scheduler/worker.  
- Add auth + audit trails for clinical usage.  
- Replace client-side pagination with server-side streaming once dataset grows beyond memory.

# Patient Monitoring System

## Prerequisites

- **Python 3.10+** (for the FastAPI backend and data loaders)
- **Node.js 18+ / npm 9+** (for the Vite + React frontend)
- **PostgreSQL 13+** with a database you can write to (e.g. `ichilov`)
- **Git**

## Full Setup: Clone ➜ Run

1. **Clone the repository**

   ```bash
   git clone <repo-url>
   cd IchilovTask
   ```

2. **Create and activate a Python virtual environment**

   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install backend dependencies**

   ```bash
   pip install -r backend/requirements.txt
   ```

4. **Configure environment variables**

   ```bash
   copy backend\.env.example backend\.env   # Windows
   # or
   cp backend/.env.example backend/.env    # macOS/Linux
   ```

   Update `backend/.env` so `DATABASE_URL` points to your PostgreSQL instance, e.g.

   ```
   DATABASE_URL=postgresql://USER:PASSWORD@localhost:5432/ichilov
   ```

   Make sure the database exists and the user has read/write permissions.

5. **Seed the database from the CSV files**

   ```bash
   python -m backend.app.db.bootstrap_db
   ```

   This creates tables and loads the sample data from `csvFiles/`.

6. **Generate monitoring/detail snapshots**

   ```bash
   python -m backend.app.db.snapshot_builder
   ```

   Run this again whenever the underlying data changes to refresh the cached payloads.

7. **Start the backend API (FastAPI + Uvicorn)**

   ```bash
   uvicorn backend.app.main:app --reload --port 8000
   ```

   - API root: `http://localhost:8000`
   - Docs: `http://localhost:8000/docs`

8. **Install frontend dependencies**

   ```bash
   cd frontend
   npm install
   ```

9. **Start the frontend dev server**

   ```bash
   npm run dev
   ```

   - Frontend: `http://localhost:3000`
   - Vite proxy forwards `/api` to `http://localhost:8000`

10. **Use the app**

    Open `http://localhost:3000` in a browser. You should see the dashboard populated with the seeded data.

> **Tip:** Keep the backend and frontend running in separate terminals. When you change CSV data or database contents, rerun the snapshot builder before refreshing the UI.

## Loading Sample CSV Data into the Database

> These steps are already included in the “Full Setup” section above. Use this reference when you only need to reseed data.

1. **Configure environment variables**  
   - Copy `backend/.env.example` to `backend/.env`.  
   - Ensure `DATABASE_URL` points to your PostgreSQL instance.

2. **Install backend dependencies (run from project root)**  
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # On macOS/Linux: source .venv/bin/activate
   pip install -r backend/requirements.txt
   ```

3. **Run the bootstrap script**  
   ```bash
   python -m backend.app.db.bootstrap_db
   ```
   - Creates all tables and loads the CSVs from `csvFiles/`.  
   - If the tables already contain data, they are cleared and reseeded automatically.

4. **Create snapshot payloads for the frontend**  
   ```bash
   python -m backend.app.db.snapshot_builder
   ```
   - Generates monitoring dashboard JSON and per-patient detail JSON.  
   - Saves payloads in `patient_monitoring_snapshots` and `patient_detail_snapshots`.

5. **Verify**  
   - Confirm the main tables and snapshot tables contain data.  
   - Rerun either script anytime after truncating tables to reload or refresh data.

## Running the Application

### Backend API

Start the FastAPI server (from project root):
```bash
uvicorn backend.app.main:app --reload --port 8000
```
- API available at `http://localhost:8000`
- Interactive API docs at `http://localhost:8000/docs`

### Frontend

1. Install dependencies (from project root):
```bash
cd frontend
npm install
```

2. Start development server:
```bash
npm run dev
```
- Frontend available at `http://localhost:3000`
- Vite proxy forwards `/api` requests to backend

## API Endpoints

- `GET /api/patients/monitoring` - Get patients requiring attention (query params: `hours_threshold`, `department`, `page`, `limit`)
- `GET /api/patients/{patient_id}` - Get detailed patient information with lab results and charts
- `GET /api/health` - Health check endpoint

## Running Tests

### Prerequisites
1. **Activate your virtual environment** (required):
   ```bash
   # On Windows:
   venv\Scripts\activate
   # On Linux/Mac:
   source venv/bin/activate
   ```

2. **Install test dependencies** (if not already installed):
   ```bash
   pip install -r backend/requirements.txt
   ```

### Running Tests

**Important**: Always use `python -m pytest` instead of just `pytest` to ensure you're using the correct Python environment.

From the project root:
```bash
# Run all tests
python -m pytest backend/tests

# Run only unit tests
python -m pytest backend/tests/unit/

# Run only integration tests
python -m pytest backend/tests/integration/

# Run with verbose output
python -m pytest backend/tests -v

# Run with coverage report
python -m pytest backend/tests --cov=backend.app --cov-report=html
```

### Troubleshooting

**"pytest is not recognized" error:**
- Make sure your virtual environment is activated
- Use `python -m pytest` instead of just `pytest`
- Verify pytest is installed: `pip list | findstr pytest` (Windows) or `pip list | grep pytest` (Linux/Mac)
- If not installed, run: `pip install -r backend/requirements.txt`

For more details, see `backend/tests/README.md`.

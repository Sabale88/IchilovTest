# Patient Monitoring System

## Loading Sample CSV Data into the Database

1. **Configure environment variables**  
   - Copy `backend/.env.example` to `backend/.env` (or export variables directly).  
   - Ensure `DATABASE_URL` points to your PostgreSQL instance, e.g.  
     ```
     postgresql://USER:PASSWORD@localhost:5432/ichilov
     ```

2. **Install backend dependencies (run from project root)**  
   ```
   python -m venv .venv
   .venv\Scripts\activate  # On macOS/Linux: source .venv/bin/activate
   pip install -r backend/requirements.txt
   ```

3. **Run the bootstrap script (still from project root)**  
   ```
   python -m backend.app.db.bootstrap_db
   ```
   - The script creates all tables and loads the CSVs from `csvFiles/`.  
   - `python-dotenv` loads `backend/.env`, so ensure `DATABASE_URL` is set there.  
   - If the tables already contain data, they are cleared and reseeded automatically.

4. **Create snapshot payloads for the frontend**  
   ```
   python -m backend.app.db.snapshot_builder
   ```
   - Generates the monitoring dashboard JSON and the per-patient drill-down JSON.  
   - Saves both payload types into `patient_monitoring_snapshots` and `patient_detail_snapshots`.

5. **Verify**  
   - Connect to the database and confirm rows exist in `patients`, `admissions`, `lab_tests`, and `lab_results`.  
   - Ensure snapshot tables contain up-to-date payloads.  
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

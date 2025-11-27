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

### 2.2 Component Breakdown

#### 2.2.1 Database Layer
- **Technology Choice**: PostgreSQL
- **Rationale**: 
  - Robust relational database with excellent support for date/time operations
  - ACID compliance for data integrity
  - Strong indexing capabilities for performance
  - JSON support for flexible schema evolution
  - Materialized snapshot tables (`patient_monitoring_snapshots`, `patient_detail_snapshots`) accelerate read-heavy workloads for the UI

#### 2.2.2 Backend Layer
- **Technology Choice**: Python with FastAPI
- **Rationale**:
  - Fast development
  - Excellent data processing libraries (pandas, SQLAlchemy)
  - Built-in async support for handling concurrent requests
  - Automatic API documentation

#### 2.2.3 Frontend Layer
- **Technology Choice**: React with TypeScript
- **Rationale**:
  - Component-based architecture
  - Rich ecosystem for data tables (e.g., Material-UI, Ant Design)
  - Strong TypeScript support for type safety

## 3. Database Schema Design

### 3.1 Entity Relationship Diagram

```
┌─────────────────────┐
│      Patients       │
├─────────────────────┤
│ patient_id (PK)     │
│ first_name          │
│ last_name           │
│ date_of_birth       │
│ primary_physician   │
│ insurance_provider  │
│ blood_type          │
│ allergies           │
└──────────┬──────────┘
           │
           │ 1:N
           │
┌──────────▼──────────┐      ┌──────────────────┐
│     Admissions      │      │    Lab Tests      │
├─────────────────────┤      ├──────────────────┤
│ case_number (PK)    │      │ test_id (PK)     │
│ patient_id (FK)     │◄─────┤ patient_id (FK)  │
│ admission_date      │      │ test_name         │
│ admission_time      │      │ order_date        │
│ release_date        │      │ order_time        │
│ release_time        │      │ ordering_physician│
│ department          │      └─────────┬─────────┘
│ room_number         │                │
└─────────────────────┘                │ 1:N
                                        │
                              ┌─────────▼─────────┐
                              │   Lab Results     │
                              ├───────────────────┤
                              │ result_id (PK)    │
                              │ test_id (FK)      │
                              │ result_value      │
                              │ result_unit       │
                              │ reference_range    │
                              │ result_status      │
                              │ performed_date     │
                              │ performed_time     │
                              │ reviewing_physician│
                              └───────────────────┘
```

### 3.2 Database Tables

#### 3.2.1 `patients` Table
```sql
CREATE TABLE patients (
    patient_id BIGINT PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    date_of_birth DATE NOT NULL,
    primary_physician VARCHAR(200),
    insurance_provider VARCHAR(100),
    blood_type VARCHAR(10),
    allergies TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL,
    INDEX idx_patient_name (last_name, first_name)
);
```

#### 3.2.2 `admissions` Table
```sql
CREATE TABLE admissions (
    hospitalization_case_number BIGINT PRIMARY KEY,
    patient_id BIGINT NOT NULL,
    admission_date DATE NOT NULL,
    admission_time TIME NOT NULL,
    release_date DATE,
    release_time TIME,
    department VARCHAR(100),
    room_number VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE,
    INDEX idx_patient_admission (patient_id, admission_date),
    INDEX idx_active_admissions (admission_date, release_date),
    INDEX idx_department (department)
);
```

#### 3.2.3 `lab_tests` Table
```sql
CREATE TABLE lab_tests (
    test_id BIGINT PRIMARY KEY,
    patient_id BIGINT NOT NULL,
    test_name VARCHAR(200) NOT NULL,
    order_date DATE NOT NULL,
    order_time TIME NOT NULL,
    ordering_physician VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE,
    INDEX idx_patient_test (patient_id, order_date, order_time),
    INDEX idx_test_date (order_date, order_time)
);
```

#### 3.2.4 `lab_results` Table
```sql
CREATE TABLE lab_results (
    result_id BIGINT PRIMARY KEY,
    test_id BIGINT NOT NULL,
    result_value DECIMAL(20, 10),
    result_unit VARCHAR(50),
    reference_range VARCHAR(200),
    result_status VARCHAR(50),
    performed_date DATE NOT NULL,
    performed_time TIME NOT NULL,
    reviewing_physician VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL,
    FOREIGN KEY (test_id) REFERENCES lab_tests(test_id) ON DELETE CASCADE,
    INDEX idx_test_result (test_id, performed_date, performed_time),
    INDEX idx_result_date (performed_date, performed_time)
);
```

#### 3.2.5 `patient_monitoring_snapshots` Table
```sql
CREATE TABLE patient_monitoring_snapshots (
    snapshot_id BIGSERIAL PRIMARY KEY,
    response_created_at TIMESTAMP NOT NULL,
    hours_threshold INT NOT NULL DEFAULT 48,
    payload JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL
);
```
*Purpose*: Stores the exact JSON payload required by the frontend dashboard (section 6.1). Each snapshot captures all **active** patients (release_date IS NULL OR release timestamp within the last 2 hours) with the fields `name`, `case_number`, `department`, `room_number`, `admission_datetime`, `hours_since_admission`, `last_test_datetime`, `hours_since_last_test`, and `last_test_name`. The backend serves the most recent snapshot for fast reads.

#### 3.2.6 `patient_detail_snapshots` Table
```sql
CREATE TABLE patient_detail_snapshots (
    snapshot_id BIGSERIAL PRIMARY KEY,
    patient_id BIGINT NOT NULL,
    response_created_at TIMESTAMP NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE,
    INDEX idx_patient_snapshot (patient_id, response_created_at DESC)
);
```
*Purpose*: Precomputes the drill-down payload per patient (section 6.2) containing contact basics, insurance provider, blood type, allergies, the latest lab result per available test (type, order date, order time, ordering physician, value, reference_range, result_status, performed_date, performed_time, reviewing_physician), and an ordered time series array for chart rendering on hover. Storing ready-to-serve JSON keeps query latency predictable.

### 3.3 Key Design Decisions

1. **Composite Date/Time Fields**: Stored separately for flexibility in queries
2. **Indexes**: Strategic indexes on foreign keys and date fields for query performance
3. **Soft Deletes**: `deleted_at` timestamp exists on every table; a scheduled job permanently purges rows once they have been soft-deleted for >30 days.
4. **Audit Fields**: `created_at` and `updated_at` ensure complete auditability and support CDC feeds if required later.

## 4. Core Business Logic

### 4.1 Query Logic: Patients Hospitalized >48 Hours Without New Tests

**Pseudocode:**
```
1. Find all active admissions (release_date IS NULL)
2. Calculate admission_datetime = admission_date + admission_time
3. Calculate hours_since_admission = NOW() - admission_datetime
4. Filter: hours_since_admission > 48 hours
5. For each patient:
   a. Find most recent lab test (MAX(order_date, order_time) or MAX(performed_date, performed_time))
   b. Calculate hours_since_last_test = NOW() - most_recent_test_datetime
   c. Filter: hours_since_last_test > 48 hours OR no tests exist
6. Return patient list with:
   - Patient information
   - Admission details
   - Hours since admission
   - Hours since last test
   - Last test performed (if any)
```

**SQL Query Concept:**
```sql
SELECT 
    p.patient_id,
    p.first_name,
    p.last_name,
    a.hospitalization_case_number,
    a.department,
    a.room_number,
    a.admission_date,
    a.admission_time,
    TIMESTAMPDIFF(HOUR, 
        CONCAT(a.admission_date, ' ', a.admission_time), 
        NOW()) AS hours_since_admission,
    MAX(GREATEST(
        CONCAT(lt.order_date, ' ', lt.order_time),
        CONCAT(lr.performed_date, ' ', lr.performed_time)
    )) AS last_test_datetime,
    TIMESTAMPDIFF(HOUR,
        COALESCE(
            MAX(GREATEST(
                CONCAT(lt.order_date, ' ', lt.order_time),
                CONCAT(lr.performed_date, ' ', lr.performed_time)
            )),
            CONCAT(a.admission_date, ' ', a.admission_time)
        ),
        NOW()) AS hours_since_last_test
FROM patients p
INNER JOIN admissions a ON p.patient_id = a.patient_id
LEFT JOIN lab_tests lt ON p.patient_id = lt.patient_id
LEFT JOIN lab_results lr ON lt.test_id = lr.test_id
WHERE a.release_date IS NULL
GROUP BY p.patient_id, a.hospitalization_case_number
HAVING hours_since_admission > 48
   AND (hours_since_last_test > 48 OR last_test_datetime IS NULL)
ORDER BY hours_since_last_test DESC;
```

### 4.2 Snapshot Generation Pipeline
1. **Patient Snapshot Builder (DO THAT)**:
   - Runs every 5 minutes.
   - Executes the query in section 4.1 for all active patients (release_date IS NULL OR release timestamp within the past 2 hours).
   - Persists the response payload and metadata into `patient_monitoring_snapshots`.
2. **Patient Detail Snapshot Builder (DO THAT)**:
   - Triggered ad-hoc (on API miss) or scheduled every 15 minutes.
   - Aggregates patient demographics plus the latest lab result for each available test, and builds ordered arrays for charting.
   - Saves the serialized JSON into `patient_detail_snapshots` keyed by patient_id.
3. **Soft Delete & Purge Job (DO THAT)**:
   - Daily job scans every table for rows where `deleted_at <= NOW() - INTERVAL '30 days'` and hard-deletes them, ensuring soft deletes only last one month while preserving compliance needs.

## 5. API Design

### 5.1 RESTful API Endpoints

#### 5.1.1 Get Patients Requiring Attention
```
GET /api/patients/monitoring
Query Parameters:
  - hours_threshold (default: 48)
  - department (optional filter)
  - page (pagination)
  - limit (page size)
  
Response:
{
  "data": [
    {
      "patient_id": 12345,
      "name": "John Doe",
      "case_number": 67890,
      "department": "Cardiology",
      "room_number": "305A",
      "admission_datetime": "2024-01-15T10:30:00",
      "hours_since_admission": 72,
      "last_test_datetime": "2024-01-15T12:00:00",
      "hours_since_last_test": 70,
      "last_test_name": "Complete Blood Count"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 50,
    "total": 25
  }
}
```
*Implementation note*: This endpoint serves the most recent record from `patient_monitoring_snapshots`, falling back to on-demand recalculation only if the cache is stale.

#### 5.1.2 Get Patient Details
```
GET /api/patients/{patient_id}
Response: Full patient information with admission and test history
```
*Implementation note*: Reads from `patient_detail_snapshots` when available, otherwise it regenerates the payload, stores a new snapshot, and returns it.

#### 5.1.3 Health Check
```
GET /api/health
Response: System status
```

## 6. Frontend Design

### 6.1 Main Dashboard View

**Components:**
1. **Header**: Title, filters (department, time threshold)
2. **Data Table**: 
   - Columns: Patient Name, Case Number, Department, Room, Hours Since Admission, Hours Since Last Test, Last Test, Actions
   - Sortable columns
   - Pagination
   - Row highlighting for critical cases (>72 hours)
3. **Summary Cards**: 
   - Total patients requiring attention
   - By department breakdown
   - Average hours since last test

### 6.2 Patient Drill-Down View

**Objectives:**
- Present richer clinical context per patient
- Surface insurance provider, blood type, allergies
- Show the most recent lab result for each available test type
- Provide a hover-enabled mini-chart of lab trendlines

**Components:**
1. **Patient Header Card**: Name, age, insurance provider, blood type, allergies, attending physician.
2. **Admission Summary**: Admission datetime, department, room, hours since admission, hours since last test, last test metadata.
3. **Recent Lab Results Table**:
   - Columns: Test Type, Order Date, Order Time, Ordering Physician, Result Value, Reference Range, Result Status, Performed Date, Performed Time, Reviewing Physician.
   - Each row includes a sparkline icon; hovering reveals the chart fed from `patient_detail_snapshots`.
4. **Trend Chart Drawer**: On hover or click, show the full timeline of the selected test with timestamps on the X-axis and values on the Y-axis, using cached JSON data.

### 6.3 User Interface Mockup (Text-based)

```
┌─────────────────────────────────────────────────────────────┐
│  Patient Monitoring Dashboard                    [Refresh]  │
├─────────────────────────────────────────────────────────────┤
│  Filters: [Department: All ▼] [Threshold: 48h ▼]          │
├─────────────────────────────────────────────────────────────┤
│  Summary: 25 patients | Cardiology: 8 | ICU: 5 | ...        │
├─────────────────────────────────────────────────────────────┤
│  Name          │ Case # │ Dept      │ Room │ Adm │ Last Test│
├─────────────────────────────────────────────────────────────┤
│  John Doe      │ 12345  │ Cardiology│ 305A │ 72h │ 70h ago │
│  Jane Smith    │ 12346  │ ICU       │ 201B │ 96h │ 95h ago │
│  ...           │ ...    │ ...       │ ...  │ ... │ ...     │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  Patient Detail: John Doe                                   │
├─────────────────────────────────────────────────────────────┤
│ Insurance: BlueCross | Blood: A+ | Allergies: Penicillin    │
│ Admission: 2024-01-15 10:30 | Dept: Cardiology | Room 305A  │
│ Hours since admission: 72 | Hours since last test: 70       │
├─────────────────────────────────────────────────────────────┤
│ Test Type │ Order Dt | Order Time | Ordering MD | Value ... │
│-------------------------------------------------------------│
│ Troponin  │ 01/15     | 12:00     | Dr. Smith   | 0.08      │◄ hover
│ CBC       │ 01/15     | 18:00     | Dr. Patel   | ...       │
└─────────────────────────────────────────────────────────────┘
           Hover sparkline → [Trend chart overlay]
```

## 7. Additional Considerations - Design Approach

*Items tagged with **(DO THAT)** are committed enhancements prioritized for implementation.*

### 7.1 Schema Changes in Source Systems

**Problem**: CSV schemas from PMS/LIS may change over time.

**Solution Design:**
1. **Schema Versioning (DO THAT)**:
   - Store schema version metadata in database
   - Maintain mapping tables for field translations
   - Use flexible JSON columns for new/unknown fields

2. **Data Validation Layer (DO THAT)**:
   - Validate CSV structure before loading
   - Log schema mismatches
   - Alert on unexpected schema changes

3. **Migration Strategy**:
   - Database migrations for schema changes
   - Backward compatibility layer
   - Gradual rollout of schema updates

### 7.2 Handling Frequent Updates (Every Few Seconds)

**Problem**: Data updates every few seconds in production.

**Solution Design:**
1. **Incremental Updates (DO THAT)**:
   - Track last processed timestamp per source
   - Process only new/changed records
   - Use database transactions for consistency

2. **Caching Strategy (DO THAT)**:
   - Cache query results (Redis/Memcached)
   - Cache invalidation on data updates
   - TTL-based refresh (e.g., 30 seconds)

3. **Real-time Updates**:
   - WebSocket/Server-Sent Events for live updates
   - Polling fallback (every 30-60 seconds)
   - Optimistic UI updates

4. **Queue System** (for production):
   - Message queue (RabbitMQ/Kafka) for async processing
   - Worker processes for data loading
   - Rate limiting to prevent overload

### 7.3 Performance Optimization

**Problem**: Thousands of patients and tests.

**Solution Design:**
1. **Database Optimization (DO THAT)**:
   - Strategic indexes (as defined in schema)
   - Query optimization (EXPLAIN ANALYZE)
   - Partitioning for large tables (by date)
   - Materialized views for complex queries

2. **Application-Level Optimization**:
   - Pagination (limit result sets)
   - Lazy loading for patient details
   - Database connection pooling
   - Query result caching

3. **Frontend Optimization**:
   - Virtual scrolling for large tables
   - Debounced search/filtering
   - Code splitting and lazy loading
   - Memoization of expensive computations

4. **Architecture Scaling**:
   - Read replicas for database
   - CDN for static assets
   - Load balancing for API servers
   - Horizontal scaling capability

## 8. Technology Stack Recommendation

### 8.1 Full Stack
- **Database**: PostgreSQL 14+
- **Backend**: Python 3.10+ with FastAPI
- **Frontend**: React 18+ with TypeScript
- **ORM**: SQLAlchemy (Python)
- **API Client**: Axios (Frontend)
- **UI Framework**: Material-UI (MUI 6)
- **Build Tools**: 
  - Backend: Poetry
  - Frontend: Vite

### 8.2 Development Tools
- **Version Control**: Git
- **Testing**: 
  - Backend: pytest
  - Frontend: Jest + React Testing Library
- **Linting**: 
  - Backend: black, flake8
  - Frontend: ESLint, Prettier
- **Documentation**: 
  - API: OpenAPI/Swagger (auto-generated by FastAPI)
  - Code: Docstrings

## 9. Security Considerations

1. **Authentication**: JWT tokens or OAuth2
2. **Authorization**: Role-based access (doctors, nurses, admins)
3. **Data Privacy**: HIPAA compliance considerations
4. **Input Validation**: Sanitize all user inputs
5. **SQL Injection**: Use parameterized queries (ORM handles this)
6. **HTTPS**: Encrypt all communications

## 10. Deployment Architecture

### 10.1 Development Environment
- Local PostgreSQL database
- Backend API on localhost:8000
- Frontend dev server on localhost:3000

### 10.2 Production Considerations
- **Containerization**: Docker for all components
- **Orchestration**: Docker Compose (simple) or Kubernetes (scalable)
- **Database**: Managed PostgreSQL service (AWS RDS, Azure Database)
- **Hosting**: 
  - Backend: AWS ECS/EC2, Heroku, Railway
  - Frontend: AWS S3 + CloudFront, Vercel, Netlify

## 11. Data Flow

### 11.1 Initial Data Load
```
CSV Files → Data Loader Script → Database
```

### 11.2 Query Flow
```
Frontend → API Request → Backend API → Database Query → 
Result Processing → JSON Response → Frontend Display
```

### 11.3 Update Flow (Future - Out of Scope)
```
S3 Event → Lambda/Worker → Process CSV → Update Database → 
Invalidate Cache → Notify Frontend (WebSocket)
```

## 12. Testing Strategy

### 12.1 Unit Tests
- Database models and relationships
- Business logic (48-hour calculation)
- API endpoints
- React components

### 12.2 Integration Tests
- API + Database integration
- Frontend + API integration
- End-to-end user flows

### 12.3 Performance Tests
- Query performance with large datasets
- API response times
- Frontend rendering performance

## 13. Monitoring and Logging

1. **Application Logging**: Structured logging (JSON format)
2. **Error Tracking**: Sentry or similar
3. **Performance Monitoring**: APM tools
4. **Database Monitoring**: Query performance metrics
5. **Health Checks**: API health endpoints

---

## Summary

This high-level design provides:
- ✅ Clear architecture with separation of concerns
- ✅ Scalable database schema with proper indexing
- ✅ RESTful API design
- ✅ Modern frontend architecture
- ✅ Solutions for schema changes, frequent updates, and performance
- ✅ Security and deployment considerations
- ✅ Testing and monitoring strategies

The design is flexible enough to accommodate future requirements while being practical for initial implementation.


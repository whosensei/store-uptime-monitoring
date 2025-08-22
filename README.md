## Store Monitoring Backend (FastAPI)

This project implements the take‑home assignment described in `instructions.md`. It exposes two endpoints to trigger and retrieve a store uptime/downtime report computed from the provided datasets in the `files/` directory.

### Features  
- **Trigger/poll** report generation with a `report_id`
- **Hourly data checking** - Checks for new data every hour
- **Auto-report generation** - Creates reports when new data is found
- **Simple uptime calculation** based on observation counting (much easier to understand)
- **Clean code structure** without over-engineering
- **Proper separation of concerns** but kept readable
- **CSV** download when complete

### Endpoints

#### Report Generation
- **POST** `/trigger_report`
  - Body: none
  - Response: `{ "report_id": "<uuid>" }`
- **GET** `/get_report?report_id=<id>`
  - If running: `{ "status": "Running" }`
  - If complete: returns the CSV file; also sets header `X-Report-Status: Complete`

#### Hourly Polling (NEW)
- **POST** `/polling/start_polling` - Start hourly data checking
- **POST** `/polling/stop_polling` - Stop hourly data checking
- **GET** `/polling/status` - Get polling status
- **GET** `/polling/last_report` - Get last auto-generated report

### Output CSV Schema
`store_id, uptime_last_hour(in minutes), uptime_last_day(in hours), uptime_last_week(in hours), downtime_last_hour(in minutes), downtime_last_day(in hours), downtime_last_week(in hours)`

### Project Structure
```
app/
  main.py                    # FastAPI app entry point
  api/report.py             # API endpoints
  models/schemas.py         # Pydantic models
  services/
    data_loader.py          # Load data from database
    calculator.py           # Simple uptime calculation
    report_service.py       # Background report generation
  database/
    models.py               # SQLAlchemy models
    config.py               # Database connection
    ingestion.py            # CSV to database loading

files/                      # Input data
  menu_hours.csv
  store_status.xlsx
  timezones.csv
  
reports/                    # Generated reports
setup_database.py           # Database setup (SQLAlchemy only)
```

### Prerequisites
- Python 3.10+
- Neon PostgreSQL (cloud database - already configured!)

### Setup & Run
```bash
# 1. Setup Python environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. Setup database (loads CSV files into Neon database)
python setup_database.py

# 3. Run the API server
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for Swagger UI.

### Generate a Report
```bash
# Trigger
curl -X POST http://127.0.0.1:8000/trigger_report
# => { "report_id": "..." }

# Poll
curl -L -o report.csv "http://127.0.0.1:8000/get_report?report_id=..."
# If still running: {"status":"Running"}
# If complete: file `report.csv` is downloaded
```

### CSV Data Locations
The app reads inputs from the `files/` directory at project root:
- `store_status.xlsx` (observations in UTC)
- `menu_hours.csv` (business hours in local time)
- `timezones.csv` (IANA timezone per store)

### Logic Summary (Simplified Approach)
- **Current time** is the max `timestamp_utc` in `store_status.xlsx` (per instructions)
- **Uptime calculation**: Count active vs inactive observations in each time window, estimate uptime as proportion
- **Much simpler** than complex interpolation - just basic counting and math
- **Business hours**: Currently assumes 24x7 (TODO: add business hours filtering for production)
- **Missing data**: No observations = assume all downtime (conservative estimate)

### Database Architecture
The application uses **Neon PostgreSQL** (serverless) as the primary data store:

**Setup Process:**
1. CSV/Excel files are loaded into Neon database during setup
2. All API requests read data from cloud database tables
3. Optimized with proper indexing for time-series queries

**Database Schema:**
- `store_status` - Time-series observations with proper indexing
- `menu_hours` - Business hours per store and day
- `store_timezones` - Timezone mapping per store

**Benefits:**
- **Serverless PostgreSQL** - auto-scaling, no server management
- **Fast indexed queries** for large datasets
- **Cloud-native** with built-in connection pooling
- **Always available** - no local setup required

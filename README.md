# QATracker — Full-Stack Python & SQLite Web Application

A full-stack QA Test Case and Defect Tracking application featuring a **Python Flask REST API** backend, **SQLite** relational database, and modern **Vanilla JavaScript SPA** frontend.

Designed specifically for Quality Engineers and Developers to manage test suites, track bugs, run automated API tests, and explore live REST endpoints.

---

## 📁 Project Architecture

```text
qa-test-tracker/
├── app.py                 # Python Flask backend server & REST API routes
├── database.py            # SQLite schema initialization, connection & seed data
├── test_tracker.db        # SQLite database file (created automatically on startup)
├── requirements.txt       # Python dependencies (Flask >= 3.0.0)
├── venv/                  # Python isolated virtual environment
├── static/                # Single Page Application (SPA) frontend
│   ├── index.html         # Responsive dashboard interface
│   ├── css/
│   │   └── style.css      # Dark/Light theme design system & cards
│   └── js/
│       └── app.js         # Fetch API client, live DOM rendering & API Explorer
├── tests/
│   └── test_api.py        # Automated Python unittest suite for REST endpoints
└── README.md              # Project manual & API documentation
```

---

## 🚀 Step 1: Starting the Backend Server

1. Open your terminal:
   ```bash
   cd "/Users/sreyasunilkumar/project/qa-test-tracker"
   ```
2. Start the Flask backend:
   ```bash
   ./venv/bin/python3 app.py
   ```
3. Open your browser and navigate to:
   ```
   http://localhost:5050
   ```

The application will automatically initialize `test_tracker.db`, create tables with foreign key constraints and indexes, and seed sample QA test cases.

---

## 🧪 Step 2: Running Automated Backend Tests

You can run the automated API test suite using Python's built-in `unittest` runner:

```bash
cd "/Users/sreyasunilkumar/project/qa-test-tracker"
./venv/bin/python3 -m unittest tests/test_api.py
```

### What the automated tests verify:
* `test_01_health_check`: Asserts `/api/health` returns HTTP 200 and database connection is healthy.
* `test_02_get_stats`: Asserts `/api/stats` computes total tests, pass rate, and defect metrics.
* `test_03_create_test_case_success`: Asserts creating a valid test case returns HTTP 201 Created.
* `test_04_create_test_case_validation_error`: Asserts missing title returns HTTP 400 Bad Request.
* `test_05_update_test_status`: Asserts updating test status updates database records.
* `test_06_create_defect`: Asserts creating a bug linked to a test case returns HTTP 201.
* `test_07_list_defects`: Asserts defects list returns HTTP 200.

---

## 📡 Step 3: REST API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Backend status, database ping, and uptime |
| `GET` | `/api/stats` | Real-time KPI metrics & passing percentages |
| `GET` | `/api/testcases` | List test cases (supports `?status=...&module=...&priority=...`) |
| `POST` | `/api/testcases` | Create a new test case |
| `GET` | `/api/testcases/<id>` | Get single test case with linked defects |
| `PUT` | `/api/testcases/<id>` | Update test case fields |
| `POST` | `/api/testcases/<id>/status` | Quick toggle status (`Passed`, `Failed`, `Blocked`, `Pending`) |
| `DELETE` | `/api/testcases/<id>` | Delete test case |
| `GET` | `/api/defects` | List all reported defects/bugs |
| `POST` | `/api/defects` | Log a new defect (optionally linked to a test case) |
| `PUT` | `/api/defects/<id>` | Update defect status (`Open`, `In Progress`, `Resolved`, `Closed`) |
| `DELETE` | `/api/defects/<id>` | Delete defect |

---

## 🔒 Security Built-in

* **SQL Injection Defense**: All database queries use parameterized SQL (`?` placeholders).
* **Security Headers**: Every response includes `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, and strict referrer headers.
* **Input Validation**: Backend strictly validates payload types, required fields, and allowed enum values before touching the database.
* **Safe Error Handling**: Handled exceptions return structured JSON errors without leaking server stack traces.

---

## 🌐 Step 4: How Backend Deployment Works

Unlike static websites (which can be hosted on GitHub Pages), full-stack apps require a persistent running server process and writable database:

* **Free / Low-Cost Cloud Platforms**:
  1. **Render.com** (Free Web Service tier, supports Python/Flask natively)
  2. **Railway.app** (One-click Git deploy with SQLite or PostgreSQL)
  3. **Fly.io** (Fast global microVM with persistent volume for SQLite)
* To run in production, simply use a production WSGI server like `gunicorn`:
  ```bash
  pip install gunicorn
  gunicorn -w 2 -b 0.0.0.0:5050 app:app
  ```

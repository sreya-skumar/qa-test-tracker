# QATracker — Full-Stack Python & SQLite Web Application

A full-stack QA Test Case and Defect Tracking application featuring a **Python Flask REST API** backend, **SQLite** relational database, and modern **Vanilla JavaScript SPA** frontend with **Multi-User Authentication and Per-User Data Isolation**.

Designed specifically for Quality Engineers and Developers to manage test suites, track bugs, run automated API tests, and explore live REST endpoints.

---

## 📁 Project Architecture

```text
qa-test-tracker/
├── app.py                 # Python Flask backend server & REST API routes
├── database.py            # SQLite schema initialization, connection & seed data
├── test_tracker.db        # SQLite database file (created automatically on startup)
├── requirements.txt       # Python dependencies (Flask, Gunicorn, Werkzeug)
├── Procfile               # Cloud deployment process declaration (Render, Railway)
├── render.yaml            # Render Blueprint for automated cloud deployment
├── venv/                  # Python isolated virtual environment
├── static/                # Single Page Application (SPA) frontend
│   ├── index.html         # Responsive dashboard interface
│   ├── login.html         # Secure login & signup interface
│   ├── css/
│   │   ├── style.css      # Dark/Light theme design system & cards
│   │   └── login.css      # Authentication UI styling
│   └── js/
│       ├── app.js         # Fetch API client, live DOM rendering & API Explorer
│       └── login.js       # Authentication controller
├── tests/
│   └── test_api.py        # 13 Automated Python unit tests (100% passing)
└── README.md              # Project manual & API documentation
```

---

## 👥 Demo User Accounts & Data Isolation

The application features full **Per-User Workspace Isolation**:
* Every user account has its own isolated test cases, defects, and KPI metrics.
* When a new user registers, they start with clean empty data (0 test cases, 0 defects, 0% stats).

| Username | Password | Role | Initial Data State |
| :--- | :--- | :--- | :--- |
| **`sreya`** | `Password123!` | Lead QA Automation Engineer | Pre-seeded with 8 sample test cases & 2 defects |
| **`alex`** | `Password123!` | QA Automation Tester | Clean slate (0 test cases, 0 defects) |
| *New Registration* | *(Any 6+ chars)* | Custom QA Role | Clean slate (0 test cases, 0 defects) |

---

## 🚀 Local Development

1. **Activate virtual environment and install dependencies**:
   ```bash
   python3 -m venv venv
   ./venv/bin/pip install -r requirements.txt
   ```

2. **Start the development server**:
   ```bash
   ./venv/bin/python3 app.py
   ```
   Or using **Gunicorn**:
   ```bash
   ./venv/bin/gunicorn app:app --bind 0.0.0.0:5050
   ```

3. **Open in browser**:
   Navigate to `http://localhost:5050/login`.

---

## 🧪 Automated Test Suite

Run the 13 automated unit tests:
```bash
./venv/bin/python3 -m unittest tests/test_api.py
```

### Verified Test Cases:
* `test_01_health_check`: Backend ping & database status.
* `test_02_get_stats`: Computes pass rates and defect metrics.
* `test_03_create_test_case_success`: Validates test case creation.
* `test_04_create_test_case_validation_error`: Asserts 400 Bad Request on invalid payloads.
* `test_05_update_test_status`: Fast status toggles.
* `test_06_create_defect`: Bug logging linked to test cases.
* `test_07_list_defects`: Lists defects.
* `test_08_login_success`: Validates session authentication.
* `test_09_login_invalid_password`: Enforces password security.
* `test_10_register_user`: New user onboarding with password hashing.
* `test_11_auth_me_and_logout`: Session lifecycle and logout.
* `test_12_new_user_has_isolated_empty_data`: Ensures multi-tenant isolation and 0-data baseline for new users.
* `test_13_unauthenticated_cannot_create_or_modify`: Asserts HTTP 401 on unauthenticated mutation attempts.

---

## ☁️ Live Cloud Deployment (Render.com)

This repository includes a `Procfile` and `render.yaml` configured for **Render**:

1. Push this repository to GitHub.
2. Log in to [Render Dashboard](https://dashboard.render.com).
3. Click **New +** -> **Web Service**.
4. Connect your GitHub repository `sreya-skumar/qa-test-tracker`.
5. Settings will auto-detect from `render.yaml`:
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app --log-file -`
6. Click **Deploy Web Service**.
7. Render will build and deploy your live URL: `https://qa-test-tracker.onrender.com`.

---

## 🔒 Security Measures

* **SQL Injection Defense**: Parameterized SQL queries throughout SQLite driver.
* **Password Hashing**: PBKDF2 with SHA-256 via Werkzeug security.
* **Session Security**: HTTPOnly, SameSite=Lax cookie configuration.
* **Security Headers**: NOSNIFF, Frame-Options DENY, strict Referrer-Policy.

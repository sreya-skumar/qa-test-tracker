"""
Database module for QA Test Case & Bug Tracker.
Manages SQLite database connections, schema setup, user isolation, and seed data.
"""

import sqlite3
import os
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_tracker.db')

def get_db():
    """Returns a connection to the SQLite database with row factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    """Initializes database tables, indexes, and migrates to user-isolated schema."""
    conn = get_db()
    cursor = conn.cursor()

    # Table 1: Users
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'QA Engineer',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Seed users if users table is empty
    cursor.execute("SELECT COUNT(*) AS count FROM users")
    if cursor.fetchone()['count'] == 0:
        seed_users(cursor)
        conn.commit()

    # Schema migration check: ensure user_id column exists on test_cases & defects
    cursor.execute("PRAGMA table_info(test_cases)")
    test_columns = [col['name'] for col in cursor.fetchall()]

    if test_columns and 'user_id' not in test_columns:
        # Migrate old schema to user-scoped schema
        cursor.execute("DROP TABLE IF EXISTS defects;")
        cursor.execute("DROP TABLE IF EXISTS test_cases;")
        conn.commit()

    # Table 2: Test Cases (isolated per user)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS test_cases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        module TEXT NOT NULL,
        priority TEXT NOT NULL CHECK(priority IN ('Critical', 'High', 'Medium', 'Low')),
        status TEXT NOT NULL DEFAULT 'Pending' CHECK(status IN ('Passed', 'Failed', 'Pending', 'Blocked')),
        automated_by TEXT NOT NULL DEFAULT 'Playwright',
        execution_time_ms INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)

    # Table 3: Defects / Bugs (isolated per user)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS defects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        test_case_id INTEGER,
        title TEXT NOT NULL,
        severity TEXT NOT NULL CHECK(severity IN ('Blocker', 'Critical', 'Major', 'Minor')),
        status TEXT NOT NULL DEFAULT 'Open' CHECK(status IN ('Open', 'In Progress', 'Resolved', 'Closed')),
        steps_to_reproduce TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (test_case_id) REFERENCES test_cases(id) ON DELETE SET NULL
    );
    """)

    # Indexes for fast querying per user
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_test_user ON test_cases(user_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_test_status ON test_cases(status);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_test_module ON test_cases(module);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_defect_user ON defects(user_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_defect_status ON defects(status);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);")

    conn.commit()

    # Seed demo test cases specifically for Sreya (user_id = 1) if Sreya has no test cases
    cursor.execute("SELECT id FROM users WHERE username = 'sreya'")
    sreya_row = cursor.fetchone()
    if sreya_row:
        sreya_id = sreya_row['id']
        cursor.execute("SELECT COUNT(*) AS count FROM test_cases WHERE user_id = ?", (sreya_id,))
        if cursor.fetchone()['count'] == 0:
            seed_data(cursor, user_id=sreya_id)
            conn.commit()

    conn.close()

def seed_users(cursor):
    """Seeds default demo users with securely hashed passwords."""
    default_password_hash = generate_password_hash("Password123!")

    sample_users = [
        (
            "sreya",
            "sreyamp14@gmail.com",
            default_password_hash,
            "Lead QA Automation Engineer"
        ),
        (
            "alex",
            "alex@example.com",
            default_password_hash,
            "QA Automation Tester"
        )
    ]

    cursor.executemany("""
    INSERT INTO users (username, email, password_hash, role)
    VALUES (?, ?, ?, ?);
    """, sample_users)

def seed_data(cursor, user_id=1):
    """Seeds initial real-world QA test cases and defects for the primary demo user."""
    sample_tests = [
        (
            user_id,
            "User Onboarding & 2FA Workspace Verification",
            "Verify new user registration triggers Twilio SMS OTP and establishes a secure authenticated session.",
            "Auth & Security",
            "Critical",
            "Passed",
            "Playwright",
            340
        ),
        (
            user_id,
            "Stripe 3D-Secure 2.0 Payment Intent Processing",
            "Ensure credit card transactions validate 3DS challenge, handle currency conversion, and record ledger entry.",
            "Fintech & Payments",
            "Critical",
            "Passed",
            "Cypress",
            145
        ),
        (
            user_id,
            "JWT Bearer Token Expiration & Replay Attack Defense",
            "Validate that expired or tampered Authorization tokens return HTTP 401 Unauthorized.",
            "REST API",
            "High",
            "Passed",
            "Postman",
            65
        ),
        (
            user_id,
            "iOS Native Biometric FaceID & Keychain Session Restore",
            "Verify Appium automated biometric authentication succeeds on native iPhone device and keeps user logged in.",
            "Mobile App",
            "High",
            "Passed",
            "Appium",
            510
        ),
        (
            user_id,
            "Stripe Webhook Event Signature Tamper Test",
            "Send mock webhook with invalid HMAC-SHA256 signature and assert HTTP 400 Bad Request.",
            "Fintech & Payments",
            "High",
            "Passed",
            "Playwright",
            92
        ),
        (
            user_id,
            "500 Concurrent Virtual Users JMeter Stress Test",
            "Verify API server sustains 500 simultaneous requests with 0% error rate and p95 latency under 400ms.",
            "Performance",
            "Medium",
            "Passed",
            "JMeter",
            1150
        ),
        (
            user_id,
            "Merchant Marketplace Loan Amortization Calculation",
            "Verify automated calculation of repayment schedules against interest rates and multi-year loan terms.",
            "Fintech & Payments",
            "High",
            "Failed",
            "Playwright",
            210
        ),
        (
            user_id,
            "Android Native Network Dropdown & Offline Queue Recovery",
            "Assert queued test transactions dispatch automatically once network connectivity is re-established.",
            "Mobile App",
            "Medium",
            "Blocked",
            "Appium",
            0
        )
    ]

    cursor.executemany("""
    INSERT INTO test_cases (user_id, title, description, module, priority, status, automated_by, execution_time_ms)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?);
    """, sample_tests)

    # Get the inserted IDs for loan calculation (test 7)
    cursor.execute("SELECT id FROM test_cases WHERE user_id = ? AND title LIKE '%Loan Amortization%'", (user_id,))
    loan_test = cursor.fetchone()
    loan_test_id = loan_test['id'] if loan_test else None

    cursor.execute("SELECT id FROM test_cases WHERE user_id = ? AND title LIKE '%Offline Queue%'", (user_id,))
    offline_test = cursor.fetchone()
    offline_test_id = offline_test['id'] if offline_test else None

    sample_defects = [
        (
            user_id,
            loan_test_id,
            "Amortization schedule rounding error on fractional cents for loan term > 36 months",
            "Critical",
            "Open",
            "1. Create loan application with $15,450.50 amount and 48 month term.\n2. Calculate amortization table.\n3. Observe penny discrepancy in final payment balance."
        ),
        (
            user_id,
            offline_test_id,
            "Appium driver socket timeout when simulating airplane mode toggle on Android 14 emulator",
            "Major",
            "In Progress",
            "1. Launch Appium session on Pixel 7 (API 34).\n2. Execute driver.set_connection(Connection.AIRPLANE_MODE).\n3. Driver fails to re-handshake after toggle."
        )
    ]

    cursor.executemany("""
    INSERT INTO defects (user_id, test_case_id, title, severity, status, steps_to_reproduce)
    VALUES (?, ?, ?, ?, ?, ?);
    """, sample_defects)

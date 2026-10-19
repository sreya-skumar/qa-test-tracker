"""
QA Test Case & Bug Tracker - Flask REST API Backend
Provides RESTful endpoints for test case management, defect tracking, and KPI metrics.
"""

import os
import time
from flask import Flask, request, jsonify, send_from_directory, session, redirect
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db, init_db

app = Flask(__name__, static_folder='static')
app.secret_key = os.environ.get('SECRET_KEY', 'qa-tracker-secret-session-key-dev-2026')
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
SERVER_START_TIME = time.time()

# --------------------------------------------------------------------------
# Security Headers Middleware
# --------------------------------------------------------------------------
@app.after_request
def apply_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response

# --------------------------------------------------------------------------
# Frontend Routes
# --------------------------------------------------------------------------
@app.route('/')
def serve_index():
    # Only authenticated users who clicked login can access the dashboard
    if not session.get('user_id'):
        return redirect('/login')
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/login')
def serve_login():
    # If already logged in, go straight to dashboard
    if session.get('user_id'):
        return redirect('/')
    return send_from_directory(app.static_folder, 'login.html')

# --------------------------------------------------------------------------
# API: Health & KPI Statistics
# --------------------------------------------------------------------------
@app.route('/api/health', methods=['GET'])
def health_check():
    """Returns backend health status, database ping, and server uptime."""
    try:
        conn = get_db()
        conn.execute("SELECT 1")
        conn.close()
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    uptime_seconds = int(time.time() - SERVER_START_TIME)

    return jsonify({
        "status": "healthy" if db_status == "connected" else "degraded",
        "database": db_status,
        "uptime_seconds": uptime_seconds,
        "framework": "Flask / Python 3",
        "version": "1.0.0"
    }), 200

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Computes real-time QA metrics and test pass rates scoped to the authenticated user."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({
            "total_test_cases": 0,
            "passed": 0,
            "failed": 0,
            "blocked": 0,
            "pending": 0,
            "pass_rate_percent": 0,
            "automation_rate_percent": 0,
            "total_defects": 0,
            "open_defects": 0,
            "critical_defects": 0
        }), 200

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT
        COUNT(*) AS total,
        SUM(CASE WHEN status = 'Passed' THEN 1 ELSE 0 END) AS passed,
        SUM(CASE WHEN status = 'Failed' THEN 1 ELSE 0 END) AS failed,
        SUM(CASE WHEN status = 'Blocked' THEN 1 ELSE 0 END) AS blocked,
        SUM(CASE WHEN status = 'Pending' THEN 1 ELSE 0 END) AS pending,
        SUM(CASE WHEN automated_by != 'Manual' THEN 1 ELSE 0 END) AS automated
    FROM test_cases
    WHERE user_id = ?;
    """, (user_id,))
    test_metrics = dict(cursor.fetchone())

    cursor.execute("""
    SELECT
        COUNT(*) AS total_defects,
        SUM(CASE WHEN status IN ('Open', 'In Progress') THEN 1 ELSE 0 END) AS open_defects,
        SUM(CASE WHEN severity = 'Critical' OR severity = 'Blocker' THEN 1 ELSE 0 END) AS critical_defects
    FROM defects
    WHERE user_id = ?;
    """, (user_id,))
    defect_metrics = dict(cursor.fetchone())

    conn.close()

    total = test_metrics['total'] or 0
    passed = test_metrics['passed'] or 0
    automated = test_metrics['automated'] or 0
    pass_rate = round((passed / total * 100), 1) if total > 0 else 0
    automation_rate = round((automated / total * 100), 1) if total > 0 else 0

    return jsonify({
        "total_test_cases": total,
        "passed": passed,
        "failed": test_metrics['failed'] or 0,
        "blocked": test_metrics['blocked'] or 0,
        "pending": test_metrics['pending'] or 0,
        "pass_rate_percent": pass_rate,
        "automation_rate_percent": automation_rate,
        "total_defects": defect_metrics['total_defects'] or 0,
        "open_defects": defect_metrics['open_defects'] or 0,
        "critical_defects": defect_metrics['critical_defects'] or 0
    }), 200

# --------------------------------------------------------------------------
# API: Authentication & User Management
# --------------------------------------------------------------------------
@app.route('/api/auth/me', methods=['GET'])
def get_current_user():
    """Returns currently authenticated user session or unauthenticated status."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"authenticated": False, "user": None}), 200

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, email, role, created_at FROM users WHERE id = ?", (user_id,))
    user_row = cursor.fetchone()
    conn.close()

    if not user_row:
        session.clear()
        return jsonify({"authenticated": False, "user": None}), 200

    return jsonify({"authenticated": True, "user": dict(user_row)}), 200

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Authenticates user via username or email and password."""
    data = request.get_json() or {}
    login_identifier = (data.get('login') or '').strip().lower()
    password = data.get('password') or ''

    if not login_identifier or not password:
        return jsonify({"error": "Please provide both username/email and password"}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM users
    WHERE LOWER(username) = ? OR LOWER(email) = ?;
    """, (login_identifier, login_identifier))
    user = cursor.fetchone()
    conn.close()

    if not user or not check_password_hash(user['password_hash'], password):
        return jsonify({"error": "Invalid username/email or password"}), 401

    session['user_id'] = user['id']
    session['username'] = user['username']

    user_data = {
        "id": user['id'],
        "username": user['username'],
        "email": user['email'],
        "role": user['role']
    }

    return jsonify({
        "message": f"Welcome back, {user['username']}!",
        "user": user_data
    }), 200

@app.route('/api/auth/register', methods=['POST'])
def register():
    """Registers a new user account with secure password hashing."""
    data = request.get_json() or {}
    username = (data.get('username') or '').strip()
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''
    role = data.get('role') or 'QA Engineer'

    if not username or len(username) < 3:
        return jsonify({"error": "Username must be at least 3 characters"}), 400
    if not email or '@' not in email:
        return jsonify({"error": "Please provide a valid email address"}), 400
    if not password or len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    conn = get_db()
    cursor = conn.cursor()

    # Check if username or email already exists
    cursor.execute("SELECT id FROM users WHERE LOWER(username) = ? OR LOWER(email) = ?", (username.lower(), email))
    if cursor.fetchone():
        conn.close()
        return jsonify({"error": "Username or email is already registered"}), 409

    password_hash = generate_password_hash(password)

    cursor.execute("""
    INSERT INTO users (username, email, password_hash, role)
    VALUES (?, ?, ?, ?);
    """, (username, email, password_hash, role))
    new_user_id = cursor.lastrowid
    conn.commit()

    cursor.execute("SELECT id, username, email, role FROM users WHERE id = ?", (new_user_id,))
    new_user = dict(cursor.fetchone())
    conn.close()

    session['user_id'] = new_user['id']
    session['username'] = new_user['username']

    return jsonify({
        "message": "Account created successfully",
        "user": new_user
    }), 201

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """Logs out current user and clears session."""
    session.clear()
    return jsonify({"message": "Successfully logged out"}), 200

# --------------------------------------------------------------------------
# API: Test Cases CRUD
# --------------------------------------------------------------------------
@app.route('/api/testcases', methods=['GET'])
def list_test_cases():
    """Lists test cases scoped to current user with optional filters for status, module, and priority."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"count": 0, "test_cases": []}), 200

    status_filter = request.args.get('status')
    module_filter = request.args.get('module')
    priority_filter = request.args.get('priority')

    query = "SELECT * FROM test_cases WHERE user_id = ?"
    params = [user_id]

    if status_filter:
        query += " AND status = ?"
        params.append(status_filter)
    if module_filter:
        query += " AND module = ?"
        params.append(module_filter)
    if priority_filter:
        query += " AND priority = ?"
        params.append(priority_filter)

    query += " ORDER BY id DESC"

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(query, params)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()

    return jsonify({"count": len(rows), "test_cases": rows}), 200

@app.route('/api/testcases', methods=['POST'])
def create_test_case():
    """Creates a new test case for the authenticated user with input validation."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Authentication required. Please log in."}), 401

    data = request.get_json() or {}

    title = (data.get('title') or '').strip()
    module = (data.get('module') or '').strip()
    priority = data.get('priority') or 'Medium'
    status = data.get('status') or 'Pending'
    automated_by = data.get('automated_by') or 'Playwright'
    description = (data.get('description') or '').strip()

    # Validation
    if not title:
        return jsonify({"error": "Title is required"}), 400
    if not module:
        return jsonify({"error": "Module is required"}), 400
    if priority not in ('Critical', 'High', 'Medium', 'Low'):
        return jsonify({"error": "Invalid priority level"}), 400
    if status not in ('Passed', 'Failed', 'Pending', 'Blocked'):
        return jsonify({"error": "Invalid status value"}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO test_cases (user_id, title, description, module, priority, status, automated_by)
    VALUES (?, ?, ?, ?, ?, ?, ?);
    """, (user_id, title, description, module, priority, status, automated_by))
    new_id = cursor.lastrowid
    conn.commit()

    cursor.execute("SELECT * FROM test_cases WHERE id = ? AND user_id = ?", (new_id, user_id))
    new_test = dict(cursor.fetchone())
    conn.close()

    return jsonify({"message": "Test case created successfully", "test_case": new_test}), 201

@app.route('/api/testcases/<int:case_id>', methods=['GET'])
def get_test_case(case_id):
    """Retrieves a single test case along with any linked defects for the user."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Authentication required"}), 401

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM test_cases WHERE id = ? AND user_id = ?", (case_id, user_id))
    test_row = cursor.fetchone()
    if not test_row:
        conn.close()
        return jsonify({"error": f"Test case #{case_id} not found"}), 404

    test_data = dict(test_row)

    cursor.execute("SELECT * FROM defects WHERE test_case_id = ? AND user_id = ? ORDER BY id DESC", (case_id, user_id))
    defects = [dict(r) for r in cursor.fetchall()]
    test_data['defects'] = defects

    conn.close()
    return jsonify({"test_case": test_data}), 200

@app.route('/api/testcases/<int:case_id>', methods=['PUT'])
def update_test_case(case_id):
    """Updates test case fields for the authenticated user."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Authentication required"}), 401

    data = request.get_json() or {}

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM test_cases WHERE id = ? AND user_id = ?", (case_id, user_id))
    existing = cursor.fetchone()
    if not existing:
        conn.close()
        return jsonify({"error": f"Test case #{case_id} not found"}), 404

    title = data.get('title', existing['title'])
    description = data.get('description', existing['description'])
    module = data.get('module', existing['module'])
    priority = data.get('priority', existing['priority'])
    status = data.get('status', existing['status'])
    automated_by = data.get('automated_by', existing['automated_by'])

    cursor.execute("""
    UPDATE test_cases
    SET title = ?, description = ?, module = ?, priority = ?, status = ?, automated_by = ?, updated_at = CURRENT_TIMESTAMP
    WHERE id = ? AND user_id = ?;
    """, (title, description, module, priority, status, automated_by, case_id, user_id))
    conn.commit()

    cursor.execute("SELECT * FROM test_cases WHERE id = ? AND user_id = ?", (case_id, user_id))
    updated_test = dict(cursor.fetchone())
    conn.close()

    return jsonify({"message": "Test case updated", "test_case": updated_test}), 200

@app.route('/api/testcases/<int:case_id>/status', methods=['POST'])
def update_test_status(case_id):
    """Quickly toggles/updates test execution status and execution time."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Authentication required"}), 401

    data = request.get_json() or {}
    new_status = data.get('status')
    execution_time = data.get('execution_time_ms', 0)

    if new_status not in ('Passed', 'Failed', 'Pending', 'Blocked'):
        return jsonify({"error": "Invalid status value"}), 400

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM test_cases WHERE id = ? AND user_id = ?", (case_id, user_id))
    if not cursor.fetchone():
        conn.close()
        return jsonify({"error": f"Test case #{case_id} not found"}), 404

    cursor.execute("""
    UPDATE test_cases
    SET status = ?, execution_time_ms = ?, updated_at = CURRENT_TIMESTAMP
    WHERE id = ? AND user_id = ?;
    """, (new_status, execution_time, case_id, user_id))
    conn.commit()

    cursor.execute("SELECT * FROM test_cases WHERE id = ? AND user_id = ?", (case_id, user_id))
    updated = dict(cursor.fetchone())
    conn.close()

    return jsonify({"message": "Test status updated", "test_case": updated}), 200

@app.route('/api/testcases/<int:case_id>', methods=['DELETE'])
def delete_test_case(case_id):
    """Deletes a test case."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Authentication required"}), 401

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM test_cases WHERE id = ? AND user_id = ?", (case_id, user_id))
    if not cursor.fetchone():
        conn.close()
        return jsonify({"error": f"Test case #{case_id} not found"}), 404

    cursor.execute("DELETE FROM test_cases WHERE id = ? AND user_id = ?", (case_id, user_id))
    conn.commit()
    conn.close()

    return jsonify({"message": f"Test case #{case_id} deleted successfully"}), 200

# --------------------------------------------------------------------------
# API: Defects / Bug Tracker CRUD
# --------------------------------------------------------------------------
@app.route('/api/defects', methods=['GET'])
def list_defects():
    """Lists defects joined with their test case title for the authenticated user."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"count": 0, "defects": []}), 200

    status_filter = request.args.get('status')
    severity_filter = request.args.get('severity')

    query = """
    SELECT d.*, t.title AS test_case_title, t.module AS test_case_module
    FROM defects d
    LEFT JOIN test_cases t ON d.test_case_id = t.id
    WHERE d.user_id = ?
    """
    params = [user_id]

    if status_filter:
        query += " AND d.status = ?"
        params.append(status_filter)
    if severity_filter:
        query += " AND d.severity = ?"
        params.append(severity_filter)

    query += " ORDER BY d.id DESC"

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(query, params)
    defects = [dict(r) for r in cursor.fetchall()]
    conn.close()

    return jsonify({"count": len(defects), "defects": defects}), 200

@app.route('/api/defects', methods=['POST'])
def create_defect():
    """Logs a new defect/bug for the authenticated user."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Authentication required. Please log in."}), 401

    data = request.get_json() or {}

    title = (data.get('title') or '').strip()
    severity = data.get('severity') or 'Major'
    status = data.get('status') or 'Open'
    test_case_id = data.get('test_case_id')
    steps = (data.get('steps_to_reproduce') or '').strip()

    if not title:
        return jsonify({"error": "Defect title is required"}), 400
    if severity not in ('Blocker', 'Critical', 'Major', 'Minor'):
        return jsonify({"error": "Invalid severity level"}), 400
    if status not in ('Open', 'In Progress', 'Resolved', 'Closed'):
        return jsonify({"error": "Invalid status value"}), 400

    conn = get_db()
    cursor = conn.cursor()

    # If test_case_id provided, ensure it belongs to this user
    if test_case_id:
        cursor.execute("SELECT id FROM test_cases WHERE id = ? AND user_id = ?", (test_case_id, user_id))
        if not cursor.fetchone():
            test_case_id = None

    cursor.execute("""
    INSERT INTO defects (user_id, test_case_id, title, severity, status, steps_to_reproduce)
    VALUES (?, ?, ?, ?, ?, ?);
    """, (user_id, test_case_id, title, severity, status, steps))
    new_id = cursor.lastrowid
    conn.commit()

    cursor.execute("SELECT * FROM defects WHERE id = ? AND user_id = ?", (new_id, user_id))
    new_defect = dict(cursor.fetchone())
    conn.close()

    return jsonify({"message": "Defect logged successfully", "defect": new_defect}), 201

@app.route('/api/defects/<int:defect_id>', methods=['PUT'])
def update_defect(defect_id):
    """Updates defect status or severity for authenticated user."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Authentication required"}), 401

    data = request.get_json() or {}

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM defects WHERE id = ? AND user_id = ?", (defect_id, user_id))
    existing = cursor.fetchone()
    if not existing:
        conn.close()
        return jsonify({"error": f"Defect #{defect_id} not found"}), 404

    title = data.get('title', existing['title'])
    severity = data.get('severity', existing['severity'])
    status = data.get('status', existing['status'])
    steps = data.get('steps_to_reproduce', existing['steps_to_reproduce'])

    cursor.execute("""
    UPDATE defects
    SET title = ?, severity = ?, status = ?, steps_to_reproduce = ?
    WHERE id = ? AND user_id = ?;
    """, (title, severity, status, steps, defect_id, user_id))
    conn.commit()

    cursor.execute("SELECT * FROM defects WHERE id = ? AND user_id = ?", (defect_id, user_id))
    updated = dict(cursor.fetchone())
    conn.close()

    return jsonify({"message": "Defect updated", "defect": updated}), 200

@app.route('/api/defects/<int:defect_id>', methods=['DELETE'])
def delete_defect(defect_id):
    """Deletes a defect."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Authentication required"}), 401

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM defects WHERE id = ? AND user_id = ?", (defect_id, user_id))
    if not cursor.fetchone():
        conn.close()
        return jsonify({"error": f"Defect #{defect_id} not found"}), 404

    cursor.execute("DELETE FROM defects WHERE id = ? AND user_id = ?", (defect_id, user_id))
    conn.commit()
    conn.close()

    return jsonify({"message": f"Defect #{defect_id} deleted successfully"}), 200

# --------------------------------------------------------------------------
# Main Entry Point
# --------------------------------------------------------------------------
if __name__ == '__main__':
    # Initialize SQLite database and seed initial test records
    init_db()
    port = int(os.environ.get('PORT', 5050))
    print(f"\n🚀 QA Test & Defect Tracker Backend starting on http://localhost:{port}\n")
    app.run(host='0.0.0.0', port=port, debug=True)

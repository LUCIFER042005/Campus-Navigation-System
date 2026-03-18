from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_cors import CORS
from flask_bcrypt import Bcrypt
import json
import sys
import functools
import webbrowser
import threading
import time
# --- Database and Logic Imports ---
from db_connector import (
    create_connection,
    read_query,
    get_all_pois,
    get_routes,
    get_current_lecture,
    get_current_events,
    initialize_db,
    save_history,
    get_history,
    get_dashboard_stats,
    get_top_searched_pois,
    get_poi_category_counts,
    get_all_dashboard_pois,
    get_all_dashboard_routes,
    create_poi,
    update_poi,
    delete_poi,
    create_route,
    update_route,
    delete_route
)

from navigation_algorithms import find_shortest_path, build_graph

# --- Flask App Initialization ---
app = Flask(__name__)
CORS(app)
def open_browser():
    # Wait 1.5 seconds for the server to initialize
    time.sleep(1.5)
    webbrowser.open("http://127.0.0.1:5000")

# Start the browser thread before the app runs
threading.Thread(target=open_browser).start()
# --- AUTHENTICATION SETUP ---
# CRITICAL: Replace this with a real, strong secret key in production
app.secret_key = 'your_strong_and_unique_secret_key_12345'
bcrypt = Bcrypt(app)

# --- HARDCODED USERS FOR ROLE-BASED ACCESS CONTROL (RBAC) ---
# ⭐ FIX: Corrected usernames and verified/regenerated password hashes for stability.

# Admin User (Full Access)
# Username: anjali / Password: password123
ADMIN_USERNAME = 'anjali'
# Hash of 'password123' (This hash was correct)
ADMIN_PASSWORD_HASH = '$2b$12$uOvDp/MLa8MldxziscfnA.1DR1aNc.yL3osuZ0AZth3QohwwWmhY2'
ADMIN_ROLE = 'admin'

# Teacher User (Limited Access - Map only)
# Username: teacher / Password: teacherpass
TEACHER_USERNAME = 'teacher'  # ⭐ FIX: Simplified username from 'teacher_user'
# Correct hash for 'teacherpass'
TEACHER_PASSWORD_HASH = '$2b$12$woHfxr.Q9sOcLuOLItMa9Ob5qD3eL9RyOpazAPQ8B3kORg4ZTDV/C'
TEACHER_ROLE = 'teacher'

# Student User (Default limited access - Map only)
# Username: student / Password: studentpass
STUDENT_USERNAME = 'student'  # ⭐ FIX: Simplified username from 'student_user'
# Correct hash for 'studentpass'
STUDENT_PASSWORD_HASH = '$2b$12$.qcPwWM5INgFc9WKk.HCs.iLWGBzCLme70OxpkELkIwFsAf9AFEQS'
STUDENT_ROLE = 'student'

# Global variable to hold the built graph structure
GRAPH_DATA = None


# --- AUTHENTICATION DECORATORS ---

def login_required(view):
    """Decorator to ensure a user is logged in."""

    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if 'logged_in' not in session or not session['logged_in']:
            return redirect(url_for('login'))
        return view(**kwargs)

    return wrapped_view


def admin_required(view):
    """Decorator to protect routes only for users with the 'admin' role."""

    @functools.wraps(view)
    @login_required  # Must be logged in first
    def wrapped_view(**kwargs):
        if session.get('role') != ADMIN_ROLE:
            return "Access Denied: Admin privileges required to manage data.", 403
        return view(**kwargs)

    return wrapped_view


# --- ROUTES ---

@app.before_request
def make_session_permanent():
    session.permanent = True


@app.route('/')
@login_required
def index():
    """Renders the main map page and passes the user role."""
    user_role = session.get('role', STUDENT_ROLE)
    return render_template('index.html', user_role=user_role)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user_role = None

        # 1. Admin Check (anjali / password123)
        if username == ADMIN_USERNAME and bcrypt.check_password_hash(ADMIN_PASSWORD_HASH, password):
            user_role = ADMIN_ROLE

        # 2. Teacher Check (teacher / teacherpass)
        elif username == TEACHER_USERNAME and bcrypt.check_password_hash(TEACHER_PASSWORD_HASH, password):
            user_role = TEACHER_ROLE

        # 3. Student Check (student / studentpass)
        elif username == STUDENT_USERNAME and bcrypt.check_password_hash(STUDENT_PASSWORD_HASH, password):
            user_role = STUDENT_ROLE

        # Successful Login
        if user_role:
            session['logged_in'] = True
            session['username'] = username
            session['role'] = user_role

            # Role-Based Redirection
            if user_role == ADMIN_ROLE:
                # Admin goes straight to the dashboard
                return redirect(url_for('admin_dashboard'))
            else:
                # Teacher and Student go to the main map page
                return redirect(url_for('index'))

        else:
            # This is the error message the user was seeing
            return render_template('login.html', error='Invalid username or password')

    if session.get('logged_in'):
        # If already logged in, redirect based on role
        if session.get('role') == ADMIN_ROLE:
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('index'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    session.pop('role', None)
    return redirect(url_for('login'))


@app.route('/admin')
@admin_required  # <-- PROTECTED: Only 'admin' role can access
def admin_dashboard():
    """Renders the admin dashboard page."""
    return render_template('admin.html')


# --- CRITICAL DB INITIALIZATION AND GRAPH BUILD ---

def rebuild_graph():
    global GRAPH_DATA
    conn = create_connection()
    if conn is None:
        print("FATAL ERROR: Cannot connect to database for initialization.", file=sys.stderr)
        return

    try:
        print("--- 1. Attempting to initialize database tables...")
        initialize_db(conn)
        print("Database tables verified.")

        # Fetch POIs and Routes to build the graph
        all_pois = read_query(conn, "SELECT poi_id, name, latitude, longitude, category, is_accessible FROM POIs")
        all_routes = get_routes(conn)
        print(f"Graph loaded with {len(all_pois)} POI nodes and {len(all_routes)} edges.")

        GRAPH_DATA = build_graph(all_pois, all_routes)
        print("Graph rebuilt successfully.")

    except Exception as e:
        print(f"Error during graph rebuild or database load: {e}", file=sys.stderr)

    finally:
        conn.close()

    return GRAPH_DATA is not None


if rebuild_graph():
    print("Server ready to calculate routes.")
else:
    print("WARNING: Server started without a fully built graph. Routing will fail.")


# --- API ROUTES (Map Access: All logged-in roles can access) ---

@app.route('/api/pois', methods=['GET'])
@login_required
def api_pois():
    conn = create_connection()
    if conn is None: return jsonify({"success": False, "message": "Database connection failed."}), 500
    try:
        pois = get_all_pois(conn)
        return jsonify({"success": True, "pois": pois})
    except Exception as e:
        print(f"Error in api_pois: {e}", file=sys.stderr)
        return jsonify({"success": False, "message": f"Internal Server Error: {e}"}), 500
    finally:
        conn.close()


@app.route('/api/route', methods=['POST'])
@login_required
def api_route():
    data = request.get_json()
    start_id = data.get('start_id')
    end_id = data.get('end_id')
    algorithm = data.get('algorithm')
    accessibility = data.get('accessible', False)

    if not all([start_id, end_id, algorithm]) or GRAPH_DATA is None:
        return jsonify({"success": False, "message": "Missing required parameters or Graph is not built."}), 400

    try:
        result = find_shortest_path(
            graph=GRAPH_DATA,
            start_id=start_id,
            end_id=end_id,
            algorithm=algorithm,
            accessible_mode=accessibility
        )

        if result and result.get('path'):
            # Convert coordinates for client-side display
            path_coords = [{'lat': coord[0], 'lng': coord[1]} for coord in result['path']]

            # Save route history
            conn = create_connection()
            if conn:
                save_history(
                    conn,
                    start_id,
                    end_id,
                    result['distance'],
                    result['distance'],  # Using distance for estimated time in this simplified case
                    algorithm,
                    accessibility
                )
                conn.close()

            return jsonify({
                "success": True,
                "path_coords": path_coords,
                "total_time": result['distance'],
                "algorithm": algorithm,
                "message": "Route found."
            })
        else:
            return jsonify({"success": False, "message": f"No path found using {algorithm}."}), 200

    except Exception as e:
        print(f"Error in api_route during path calculation: {e}", file=sys.stderr)
        return jsonify({"success": False, "message": f"Internal Server Error during routing: {e}"}), 500


@app.route('/api/history', methods=['GET'])
@login_required
def api_history():
    conn = create_connection()
    if conn is None: return jsonify({"success": False, "message": "Database connection failed."}), 500
    try:
        history_records = get_history(conn)
        return jsonify({"success": True, "history": history_records})
    except Exception as e:
        print(f"Error fetching history: {e}", file=sys.stderr)
        return jsonify({"success": False, "message": "Failed to fetch history."}), 500
    finally:
        conn.close()


@app.route('/api/status', methods=['GET'])
@login_required
def api_status():
    conn = create_connection()
    if conn is None: return jsonify({"success": False, "message": "Database connection failed."}), 500
    try:
        lecture_data = get_current_lecture(conn)
        event_data = get_current_events(conn)

        return jsonify({
            "success": True,
            "lecture": lecture_data,
            "events": event_data
        })
    finally:
        conn.close()


# --- ADMIN DASHBOARD API ROUTES (Protected: Only Admin can access) ---

@app.route('/api/dashboard_stats', methods=['GET'])
@admin_required
def dashboard_stats():
    conn = create_connection()
    if conn is None: return jsonify({'success': False, 'message': 'Database connection failed for stats.'}), 500
    try:
        stats = get_dashboard_stats(conn)
        top_pois = get_top_searched_pois(conn)
        category_counts = get_poi_category_counts(conn)

        return jsonify({
            'success': True,
            'stats': stats,
            'top_pois': top_pois,
            'category_counts': category_counts
        })

    except Exception as e:
        print(f"Error fetching dashboard stats: {e}", file=sys.stderr)
        return jsonify({'success': False, 'message': f"Internal Server Error: {str(e)}"}), 500
    finally:
        conn.close()


@app.route('/api/pois/data', methods=['GET'])
@admin_required
def api_poi_data():
    conn = create_connection()
    if conn is None: return jsonify({'success': False, 'message': 'Database connection failed.'}), 500
    try:
        pois = get_all_dashboard_pois(conn)
        return jsonify({'success': True, 'data': pois})
    except Exception as e:
        print(f"Error fetching all POI data: {e}", file=sys.stderr)
        return jsonify({'success': False, 'message': f'Internal Server Error: {str(e)}'}), 500
    finally:
        conn.close()


@app.route('/api/routes/data', methods=['GET'])
@admin_required
def api_route_data():
    conn = create_connection()
    if conn is None: return jsonify({'success': False, 'message': 'Database connection failed.'}), 500
    try:
        routes = get_all_dashboard_routes(conn)
        return jsonify({'success': True, 'data': routes})
    except Exception as e:
        print(f"Error fetching all Route data: {e}", file=sys.stderr)
        return jsonify({'success': False, 'message': f'Internal Server Error: {str(e)}'}), 500
    finally:
        conn.close()


# --- ADMIN DASHBOARD CRUD API ROUTES (Protected: Only Admin can access) ---

@app.route('/api/poi/create', methods=['POST'])
@admin_required  # Protected
def api_poi_create():
    conn = create_connection()
    if conn is None: return jsonify({'success': False, 'message': 'Database connection failed.'}), 500
    try:
        data = request.get_json()
        if create_poi(conn, data):
            rebuild_graph()  # Rebuild graph on successful creation
            return jsonify({'success': True, 'message': 'POI created successfully.'})
        return jsonify({'success': False, 'message': 'Failed to create POI (Check for duplicate POI ID).'})
    except Exception as e:
        print(f"Error creating POI: {e}", file=sys.stderr)
        return jsonify({'success': False, 'message': f'Error creating POI: {str(e)}'}), 500
    finally:
        conn.close()


@app.route('/api/poi/update', methods=['POST'])
@admin_required  # Protected
def api_poi_update():
    conn = create_connection()
    if conn is None: return jsonify({'success': False, 'message': 'Database connection failed.'}), 500
    try:
        data = request.get_json()
        if update_poi(conn, data):
            rebuild_graph()  # Rebuild graph on successful update
            return jsonify({'success': True, 'message': 'POI updated successfully.'})
        return jsonify({'success': False, 'message': 'Failed to update POI.'})
    except Exception as e:
        print(f"Error updating POI: {e}", file=sys.stderr)
        return jsonify({'success': False, 'message': f'Error updating POI: {str(e)}'}), 500
    finally:
        conn.close()


@app.route('/api/poi/delete', methods=['POST'])
@admin_required  # Protected
def api_poi_delete():
    conn = create_connection()
    if conn is None: return jsonify({'success': False, 'message': 'Database connection failed.'}), 500
    try:
        data = request.get_json()
        poi_id = data.get('poi_id')
        if delete_poi(conn, poi_id):
            rebuild_graph()  # Rebuild graph on successful deletion
            return jsonify({'success': True, 'message': 'POI and related routes deleted successfully.'})
        return jsonify({'success': False, 'message': 'Failed to delete POI.'})
    except Exception as e:
        print(f"Error deleting POI: {e}", file=sys.stderr)
        return jsonify({'success': False, 'message': f'Error deleting POI: {str(e)}'}), 500
    finally:
        conn.close()


@app.route('/api/route/create', methods=['POST'])
@admin_required  # Protected
def api_route_create():
    conn = create_connection()
    if conn is None: return jsonify({'success': False, 'message': 'Database connection failed.'}), 500
    try:
        data = request.get_json()
        # Create route A -> B
        success_ab = create_route(conn, data)

        # Create route B -> A (for bidirectional)
        data_ba = data.copy()
        data_ba['poi_id_a'], data_ba['poi_id_b'] = data['poi_id_b'], data['poi_id_a']
        success_ba = create_route(conn, data_ba)

        if success_ab and success_ba:
            rebuild_graph()  # Rebuild graph on successful creation
            return jsonify({'success': True, 'message': 'Bidirectional route created successfully.'})
        return jsonify({'success': False, 'message': 'Failed to create route(s).'})
    except Exception as e:
        print(f"Error creating route: {e}", file=sys.stderr)
        return jsonify({'success': False, 'message': f'Error creating route: {str(e)}'}), 500
    finally:
        conn.close()


@app.route('/api/route/update', methods=['POST'])
@admin_required  # Protected
def api_route_update():
    conn = create_connection()
    if conn is None: return jsonify({'success': False, 'message': 'Database connection failed.'}), 500
    try:
        data = request.get_json()
        if update_route(conn, data):
            rebuild_graph()  # Rebuild graph on successful update
            return jsonify({'success': True, 'message': 'Route updated successfully.'})
        return jsonify({'success': False, 'message': 'Failed to update route.'})
    except Exception as e:
        print(f"Error updating route: {e}", file=sys.stderr)
        return jsonify({'success': False, 'message': f'Error updating route: {str(e)}'}), 500
    finally:
        conn.close()


@app.route('/api/route/delete', methods=['POST'])
@admin_required  # Protected
def api_route_delete():
    conn = create_connection()
    if conn is None: return jsonify({'success': False, 'message': 'Database connection failed.'}), 500
    try:
        data = request.get_json()
        route_id = data.get('route_id')
        if delete_route(conn, route_id):
            rebuild_graph()  # Rebuild graph on successful deletion
            return jsonify({'success': True, 'message': 'Route deleted successfully.'})
        return jsonify({'success': False, 'message': 'Failed to delete route.'})
    except Exception as e:
        print(f"Error deleting route: {e}", file=sys.stderr)
        return jsonify({'success': False, 'message': f'Error deleting route: {str(e)}'}), 500
    finally:
        conn.close()


# --- Run Server ---
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)


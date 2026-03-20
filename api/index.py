from flask import Flask, render_template, request, jsonify
import mysql.connector
import os

# --- VERCEL PATH FIX START ---
# Absolute paths ensure Vercel finds your HTML/CSS even inside the /api folder
base_dir = os.path.dirname(os.path.abspath(__file__))
template_dir = os.path.join(base_dir, '../templates')
static_dir = os.path.join(base_dir, '../static')

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
# --- VERCEL PATH FIX END ---

def get_db_connection():
    """Establishes connection to TiDB Cloud using Environment Variables"""
    return mysql.connector.connect(
        host="gateway01.ap-southeast-1.prod.aws.tidbcloud.com",
        port=4000,
        user="3nPLoNR3Ghr6MfH.root",
        password=os.environ.get('TIDB_PASSWORD'),
        database="smart_campus_db",
        ssl_verify_cert=True,
        autocommit=True
    )

@app.route('/')
def home():
    """Serves the main Map page"""
    return render_template('index.html')

@app.route('/get_locations')
def get_locations():
    """Fetches all building names from TiDB for the dropdown menus"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        # Note: Change 'nodes' to your actual table name if it is different
        cursor.execute("SELECT DISTINCT name FROM nodes WHERE name IS NOT NULL ORDER BY name ASC")
        locations = cursor.fetchall()
        return jsonify(locations)
    except Exception as e:
        print(f"Database Error: {e}")
        return jsonify([]) # Return empty list if DB fails
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@app.route('/logout')
def logout():
    """Prevents the 'logout' BuildError in your HTML"""
    return "Logged out successfully! <a href='/'>Go back home</a>"

# --- OPTIONAL: ADD YOUR NAVIGATION ROUTE BELOW ---
# If your JS calls /navigate or /find_path, you should paste that code here!
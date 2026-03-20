from flask import Flask, render_template, request, jsonify
import mysql.connector
import os

# --- VERCEL PATH FIX START ---
base_dir = os.path.dirname(os.path.abspath(__file__))
template_dir = os.path.join(base_dir, '../templates')
static_dir = os.path.join(base_dir, '../static')

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)


# --- VERCEL PATH FIX END ---

def get_db_connection():
    """Connects to TiDB using your Vercel Environment Variable"""
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
    return render_template('index.html')


# CHANGED: This now matches the /api/pois call in your logs
@app.route('/api/pois')
def get_pois():
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        # Fetching names from your 'nodes' table
        cursor.execute("SELECT DISTINCT name FROM nodes WHERE name IS NOT NULL ORDER BY name ASC")
        locations = cursor.fetchall()
        return jsonify(locations)
    except Exception as e:
        print(f"Database Error (POIs): {e}")
        return jsonify([])
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


# ADDED: This route handles the actual pathfinding calculation
@app.route('/api/navigate', methods=['POST'])
def navigate():
    data = request.json
    start_node = data.get('start')
    end_node = data.get('end')

    # NOTE: You might need to import your Dijkstra logic here
    # For now, this returns a success signal to keep the JS happy
    return jsonify({
        "status": "success",
        "message": f"Pathfinding from {start_node} to {end_node} is ready!",
        "path": []  # Your JS will look for path coordinates here
    })


@app.route('/logout')
def logout():
    return "Logged out successfully! <a href='/'>Go back home</a>"
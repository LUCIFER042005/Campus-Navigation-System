from flask import Flask, render_template, request, jsonify
import mysql.connector
import os

# --- VERCEL PATH FIX ---
base_dir = os.path.dirname(os.path.abspath(__file__))
template_dir = os.path.join(base_dir, '../templates')
static_dir = os.path.join(base_dir, '../static')

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

def get_db_connection():
    """Connects to TiDB Cloud using your Vercel Environment Variable"""
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
    """Serves your main index.html file"""
    return render_template('index.html')

@app.route('/api/pois')
def get_pois():
    """Fetches building names for your dropdown menus"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        # Fetching ID and Name for the dropdowns
        query = "SELECT id, name FROM nodes WHERE name IS NOT NULL AND name != '' ORDER BY name ASC"
        cursor.execute(query)
        locations = cursor.fetchall()
        return jsonify(locations)
    except Exception as e:
        print(f"DATABASE ERROR (POIs): {e}")
        return jsonify([])
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@app.route('/api/navigate', methods=['POST'])
def navigate():
    """Fetches coordinates and prepares the path for the map to draw"""
    conn = None
    cursor = None
    try:
        data = request.json
        start_name = data.get('start')
        end_name = data.get('end')

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # 1. Get coordinates for Start point
        cursor.execute("SELECT latitude, longitude FROM nodes WHERE name = %s", (start_name,))
        start_node = cursor.fetchone()

        # 2. Get coordinates for Destination
        cursor.execute("SELECT latitude, longitude FROM nodes WHERE name = %s", (end_name,))
        end_node = cursor.fetchone()

        if not start_node or not end_node:
            return jsonify({"status": "error", "message": "Location not found in TiDB"})

        # 3. Create the path coordinates [ [lat, lng], [lat, lng] ]
        # This format is exactly what Leaflet (L.polyline) needs
        path_coords = [
            [float(start_node['latitude']), float(start_node['longitude'])],
            [float(end_node['latitude']), float(end_node['longitude'])]
        ]

        return jsonify({
            "status": "success",
            "path": path_coords,
            "message": f"Routing from {start_name} to {end_name}"
        })
    except Exception as e:
        print(f"NAVIGATION ERROR: {e}")
        return jsonify({"status": "error", "message": str(e)})
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@app.route('/logout')
def logout():
    """Redirects or shows logout message"""
    return "Logged out! <a href='/'>Go back to Map</a>"

if __name__ == "__main__":
    app.run(debug=True)
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
    return render_template('index.html')


@app.route('/api/pois')
def get_pois():
    """Fetches building names for the dropdowns"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # We use DISTINCT to avoid duplicates and check for empty names
        # IMPORTANT: Make sure your table is named 'nodes' in TiDB!
        query = "SELECT DISTINCT name FROM nodes WHERE name IS NOT NULL AND name != '' ORDER BY name ASC"
        cursor.execute(query)

        locations = cursor.fetchall()
        print(f"DEBUG: Found {len(locations)} locations in database.")
        return jsonify(locations)
    except Exception as e:
        print(f"DATABASE ERROR: {e}")
        return jsonify([])  # Return empty list so the site doesn't crash
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


@app.route('/api/navigate', methods=['POST'])
def navigate():
    """Handles the pathfinding request when you click 'Find Route'"""
    try:
        data = request.json
        start_point = data.get('start')
        end_point = data.get('end')

        # For now, we return a success message.
        # Later, we can add your Dijkstra algorithm logic here!
        return jsonify({
            "status": "success",
            "path": [],  # If you have a list of coordinates, put them here
            "message": f"Calculating path from {start_point} to {end_point}"
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@app.route('/logout')
def logout():
    return "Logged out! <a href='/'>Go back to Map</a>"


if __name__ == "__main__":
    app.run(debug=True)
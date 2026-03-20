from flask import Flask, render_template, request, jsonify
import mysql.connector
import os

app = Flask(__name__)

def get_db_connection():
    # We use '3nPLoNR3Ghr6MfH.root' as the user and 'smart_campus_db' as the database
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
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        # We select ID and Name for the dropdown
        cursor.execute("SELECT id, name FROM nodes WHERE name IS NOT NULL")
        locations = cursor.fetchall()
        return jsonify(locations)
    except Exception as e:
        # This will show in your Vercel Logs if it fails
        print(f"ERROR: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

# ... (keep your navigate route below this)
from flask import Flask, render_template, request, jsonify
import mysql.connector
import os

# --- VERCEL PATH FIX START ---
# We use absolute paths because Vercel's Linux servers are picky about folder locations
base_dir = os.path.dirname(os.path.abspath(__file__))
template_dir = os.path.join(base_dir, '../templates')
static_dir = os.path.join(base_dir, '../static')

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
# --- VERCEL PATH FIX END ---

def get_db_connection():
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

# --- ADDED THIS ROUTE TO PREVENT THE 500 ERROR ---
# Your index.html was looking for 'logout', so we must define it here.
@app.route('/logout')
def logout():
    # For now, it just says this. You can make it redirect later!
    return "Logged out successfully! <a href='/'>Go back home</a>"

# If you have other routes (like /login or /navigate), add them below here!
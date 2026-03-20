from flask import Flask, render_template, request, jsonify
import mysql.connector
import os

app = Flask(__name__, template_folder='../templates', static_folder='../static')
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


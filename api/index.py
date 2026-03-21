import os
from flask import Flask, render_template, request, jsonify
import mysql.connector
import networkx as nx

# Critical: tells Flask to look for folders in the root
app = Flask(__name__,
            template_folder='../templates',
            static_folder='../static')


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


@app.route('/logout')
def logout():
    # This just sends them back to the home page for now
    return render_template('index.html')

@app.route('/api/pois')
def get_pois():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, name FROM nodes WHERE name IS NOT NULL")
        return jsonify(cursor.fetchall())
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()


@app.route('/api/navigate')
def navigate():
    start_id = request.args.get('start')
    end_id = request.args.get('end')
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Get all nodes and edges to build the map graph
        cursor.execute("SELECT id, latitude, longitude FROM nodes")
        nodes = cursor.fetchall()
        cursor.execute("SELECT start_node, end_node, weight FROM edges")
        edges = cursor.fetchall()

        G = nx.Graph()
        for node in nodes:
            G.add_node(node['id'], pos=(float(node['latitude']), float(node['longitude'])))
        for edge in edges:
            G.add_edge(edge['start_node'], edge['end_node'], weight=float(edge['weight']))

        # Dijkstra Calculation
        path_ids = nx.shortest_path(G, source=int(start_id), target=int(end_id), weight='weight')

        # Convert path IDs back to coordinates for the map
        node_dict = {n['id']: [float(n['latitude']), float(n['longitude'])] for n in nodes}
        path_coords = [node_dict[node_id] for node_id in path_ids]

        return jsonify({"path": path_coords})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()
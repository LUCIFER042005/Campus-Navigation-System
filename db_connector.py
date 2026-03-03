import mysql.connector
import sys
import json
import os
from mysql.connector import Error
from datetime import datetime

# --- CRITICAL: MySQL Configuration ---
# Verify these settings match your XAMPP/MySQL setup.
MYSQL_CONFIG = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': '',  # Default XAMPP password is often blank.
    'database': 'smart_campus_db'  # Must match the database name you created in phpMyAdmin.
}

# Name of the JSON file containing the campus map data
JSON_FILE = 'campus_nodes_edges.json'




# --- Connection Functions ---

def create_connection():
    """Creates and returns a connection object to the MySQL database."""
    conn = None
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        if conn and conn.is_connected():
            return conn
    except Error as e:
        print(f"FATAL: Database connection error: {e}. Check your MYSQL_CONFIG and ensure MySQL is running.",
              file=sys.stderr)
        return None
    return None


def execute_query(connection, query, params=()):
    """Executes a single write query (INSERT, UPDATE, DELETE) on the database."""
    if connection is None:
        return False
    try:
        cursor = connection.cursor()
        cursor.execute(query, params)
        connection.commit()
        return True
    except Error as e:
        print(f"!!! CRITICAL DATABASE WRITE ERROR: {e}. Query: {query} Params: {params}", file=sys.stderr)
        return False


def read_query(connection, query, params=()):
    """Executes a read query (SELECT) and returns the results as a list of dictionaries."""
    if connection is None:
        return []
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, params)
        results = cursor.fetchall()
        return results
    except Error as e:
        print(f"Database read error: {e}", file=sys.stderr)
        return []


# --- JSON Data Loading Function ---

def load_initial_data_from_json(connection):
    """
    Reads POI and Route data from the campus_nodes_edges.json file
    and inserts it into the MySQL tables if they are empty.
    """
    if connection is None:
        print("Skipping JSON load: No database connection.", file=sys.stderr)
        return False

    # Check if POIs table is empty
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM POIs")
        result = cursor.fetchone()
        if result and result[0] > 0:
            print("POI table already contains data. Skipping JSON insertion.")
            return True
    except Error as e:
        # This is expected if the table was just dropped or doesn't exist yet
        print(f"Checking POIs table failed, continuing initialization: {e}", file=sys.stderr)

    if not os.path.exists(JSON_FILE):
        print(f"CRITICAL: JSON data file not found: {JSON_FILE}", file=sys.stderr)
        return False

    try:
        with open(JSON_FILE, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"CRITICAL: Failed to load {JSON_FILE}: {e}", file=sys.stderr)
        return False

    print("Inserting POI nodes and Route edges from JSON...")

    # Insert POI Nodes
    poi_insert_sql = """
    INSERT INTO POIs (poi_id, name, latitude, longitude, category, is_accessible, building_id, floor)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE name=VALUES(name)
    """
    node_count = 0
    for node in data['nodes']:
        is_accessible = 1 if node.get('accessible') else 0

        params = (
            node['id'],
            node.get('name', f"POI {node['id']}"),
            node['lat'],
            node['lng'],
            node.get('type', 'path'),
            is_accessible,
            node.get('building_id'),
            node.get('floor')
        )
        execute_query(connection, poi_insert_sql, params)
        node_count += 1

    # Insert Routes (Edges)
    route_insert_sql = """
    INSERT INTO Routes (poi_id_a, poi_id_b, distance_m, travel_time_min, is_accessible)
    VALUES (%s, %s, %s, %s, %s)
    """
    edge_count = 0
    for edge in data['edges']:
        is_accessible = 1 if edge.get('accessible') else 0

        # Insert edge A -> B
        params_ab = (edge['from'], edge['to'], edge['distance'], edge['time'], is_accessible)
        execute_query(connection, route_insert_sql, params_ab)
        edge_count += 1

        # Insert edge B -> A (bidirectional path)
        params_ba = (edge['to'], edge['from'], edge['distance'], edge['time'], is_accessible)
        execute_query(connection, route_insert_sql, params_ba)
        edge_count += 1

    connection.commit()
    print(f"Successfully inserted {node_count} POI nodes and {edge_count} Route edges into MySQL.")
    return True


# --- POI and Route Management Functions (Read) ---

def get_all_pois(connection):
    # This fetches data for the main map's dropdowns
    select_query = """
    SELECT 
        MIN(poi_id) AS id,     
        name, 
        MAX(latitude) AS lat,  
        MAX(longitude) AS lng  
    FROM 
        POIs 
    WHERE 
        category NOT IN ('Path', 'Entrance') 
        AND name IS NOT NULL AND name <> '' 
        AND latitude IS NOT NULL 
        AND longitude IS NOT NULL
        AND latitude <> 0 
        AND longitude <> 0 
    GROUP BY 
        name  
    ORDER BY 
        name ASC;
    """
    return read_query(connection, select_query)


def get_routes(connection):
    # This fetches all routes for the graph builder
    query = "SELECT poi_id_a, poi_id_b, distance_m, travel_time_min, is_accessible FROM Routes"
    return read_query(connection, query)


# --- Admin Dashboard Helper Functions (Read for Tables) ---

def get_all_dashboard_pois(connection):
    """Fetches all POI details for the admin dashboard table."""
    query = """
    SELECT 
        poi_id, 
        name, 
        category, 
        latitude, 
        longitude, 
        is_accessible,
        building_id,
        floor
    FROM 
        POIs 
    ORDER BY 
        poi_id ASC;
    """
    return read_query(connection, query)


def get_all_dashboard_routes(connection):
    """Fetches all Route details for the admin dashboard table."""
    query = """
    SELECT 
        route_id, 
        poi_id_a, 
        poi_id_b, 
        distance_m, 
        travel_time_min, 
        is_accessible 
    FROM 
        Routes 
    ORDER BY 
        route_id ASC;
    """
    return read_query(connection, query)


# ====================================================================
# --- POI CRUD FUNCTIONS ---
# ====================================================================

def create_poi(connection, poi_data):
    """Creates a new POI record (C in CRUD)."""
    query = """
    INSERT INTO POIs 
        (poi_id, name, latitude, longitude, category, is_accessible, building_id, floor)
    VALUES 
        (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    params = (
        poi_data['poi_id'], poi_data['name'], poi_data['latitude'], poi_data['longitude'],
        poi_data['category'], int(poi_data['is_accessible']), poi_data['building_id'], poi_data['floor']
    )
    return execute_query(connection, query, params)


def update_poi(connection, poi_data):
    """Updates an existing POI record (U in CRUD)."""
    query = """
    UPDATE POIs SET 
        name = %s, 
        latitude = %s, 
        longitude = %s, 
        category = %s, 
        is_accessible = %s,
        building_id = %s,
        floor = %s
    WHERE poi_id = %s
    """
    params = (
        poi_data['name'], poi_data['latitude'], poi_data['longitude'],
        poi_data['category'], int(poi_data['is_accessible']), poi_data['building_id'],
        poi_data['floor'], poi_data['poi_id']
    )
    return execute_query(connection, query, params)


def delete_poi(connection, poi_id):
    """Deletes a POI record (D in CRUD) and its dependent routes."""
    # 1. First, delete all dependent routes referencing this POI
    delete_routes_query = "DELETE FROM Routes WHERE poi_id_a = %s OR poi_id_b = %s"
    execute_query(connection, delete_routes_query, (poi_id, poi_id))

    # 2. Then, delete the POI itself
    delete_poi_query = "DELETE FROM POIs WHERE poi_id = %s"
    return execute_query(connection, delete_poi_query, (poi_id,))


# ====================================================================
# --- ROUTE CRUD FUNCTIONS ---
# ====================================================================

def create_route(connection, route_data):
    """Creates a new Route record (C in CRUD)."""
    query = """
    INSERT INTO Routes 
        (poi_id_a, poi_id_b, distance_m, travel_time_min, is_accessible)
    VALUES 
        (%s, %s, %s, %s, %s)
    """
    params = (
        route_data['poi_id_a'], route_data['poi_id_b'], route_data['distance_m'],
        route_data['travel_time_min'], int(route_data['is_accessible'])
    )
    return execute_query(connection, query, params)


def update_route(connection, route_data):
    """Updates an existing Route record (U in CRUD)."""
    query = """
    UPDATE Routes SET 
        poi_id_a = %s, 
        poi_id_b = %s, 
        distance_m = %s, 
        travel_time_min = %s, 
        is_accessible = %s
    WHERE route_id = %s
    """
    params = (
        route_data['poi_id_a'], route_data['poi_id_b'], route_data['distance_m'],
        route_data['travel_time_min'], int(route_data['is_accessible']), route_data['route_id']
    )
    return execute_query(connection, query, params)


def delete_route(connection, route_id):
    """Deletes a Route record (D in CRUD)."""
    query = "DELETE FROM Routes WHERE route_id = %s"
    return execute_query(connection, query, (route_id,))


# ====================================================================
# --- HISTORY AND STATUS FUNCTIONS (FIXED/RE-ADDED) ---
# ====================================================================

def save_history(connection, start_id, end_id, distance, travel_time, algorithm, is_accessible):
    """Saves a route search event to the searchhistory table."""
    query = """
    INSERT INTO searchhistory 
        (start_poi_id, end_poi_id, distance_m, travel_time_min, algorithm, is_accessible)
    VALUES 
        (%s, %s, %s, %s, %s, %s)
    """
    params = (
        start_id,
        end_id,
        distance,
        travel_time,
        algorithm,
        int(is_accessible)
    )
    return execute_query(connection, query, params)


def get_history(connection):
    """Retrieves the last 10 search history records with POI names."""
    query = """
    SELECT 
        sh.history_id,
        sh.search_time,
        sh.distance_m,
        sh.travel_time_min,
        sh.algorithm,
        start_poi.name AS start_name,
        end_poi.name AS end_name
    FROM 
        searchhistory sh
    JOIN 
        POIs start_poi ON sh.start_poi_id = start_poi.poi_id
    JOIN 
        POIs end_poi ON sh.end_poi_id = end_poi.poi_id
    ORDER BY 
        sh.search_time DESC
    LIMIT 10;
    """
    return read_query(connection, query)


def get_current_lecture(connection):
    """Placeholder function to simulate fetching current lecture status."""
    # This is dummy data, as requested by app_server.py
    return {
        'status': 'In Session',
        'details': 'CS 101 - Algorithms in Room 301, Engineering Hall',
        'next': 'Math 202 at 10:00 AM'
    }


def get_current_events(connection):
    """Placeholder function to simulate fetching current campus events."""
    # This is dummy data, as requested by app_server.py
    return {
        'today': 'Student Union Job Fair (9am - 3pm)',
        'upcoming': 'Graduation Ceremony Practice (Main Field, Tomorrow)'
    }


# --- Dashboard Statistics Functions ---

def get_dashboard_stats(connection):
    """Calculates overall route search statistics."""
    query = """
    SELECT 
        COUNT(*) AS total_searches,
        SUM(CASE WHEN is_accessible = 1 THEN 1 ELSE 0 END) AS accessible_searches,
        COUNT(DISTINCT CONCAT(start_poi_id, '-', end_poi_id)) AS unique_routes_searched
    FROM 
        searchhistory;
    """
    # Use read_query and return the first result dictionary
    stats = read_query(connection, query)
    return stats[0] if stats else {
        'total_searches': 0,
        'accessible_searches': 0,
        'unique_routes_searched': 0
    }


def get_top_searched_pois(connection, limit=5):
    """Finds the top starting and ending POIs."""
    # Query for Top Starting Points
    start_query = """
    SELECT 
        p.name AS poi_name, 
        COUNT(sh.start_poi_id) AS search_count
    FROM 
        searchhistory sh
    JOIN 
        POIs p ON sh.start_poi_id = p.poi_id
    GROUP BY 
        sh.start_poi_id
    ORDER BY 
        search_count DESC
    LIMIT %s;
    """
    top_starts = read_query(connection, start_query, (limit,))

    # Query for Top Destinations
    end_query = """
    SELECT 
        p.name AS poi_name, 
        COUNT(sh.end_poi_id) AS search_count
    FROM 
        searchhistory sh
    JOIN 
        POIs p ON sh.end_poi_id = p.poi_id
    GROUP BY 
        sh.end_poi_id
    ORDER BY 
        search_count DESC
    LIMIT %s;
    """
    top_ends = read_query(connection, end_query, (limit,))

    return {'top_starts': top_starts, 'top_ends': top_ends}


def get_poi_category_counts(connection):
    """Counts the number of POIs in each category."""
    query = """
    SELECT 
        category, 
        COUNT(*) AS count 
    FROM 
        POIs 
    WHERE 
        category NOT IN ('Path', 'Entrance') 
    GROUP BY 
        category 
    ORDER BY 
        count DESC;
    """
    return read_query(connection, query)


# ====================================================================
# --- Database Initialization (Unchanged) ---
# ====================================================================

def initialize_db(connection):
    # ... (function body for initialize_db remains the same)
    if connection is None: return False

    try:
        cursor = connection.cursor()
        cursor.execute(f"USE {MYSQL_CONFIG['database']}")
        connection.database = MYSQL_CONFIG['database']
    except Error as e:
        print(f"Error selecting database '{MYSQL_CONFIG['database']}': {e}. Ensure the database exists in MySQL.",
              file=sys.stderr)
        return False

    poi_table_query = """
    CREATE TABLE IF NOT EXISTS POIs (
        poi_id INT PRIMARY KEY,
        building_id INT,
        name VARCHAR(100) NOT NULL,
        floor INT,
        category VARCHAR(50) NOT NULL,
        is_accessible TINYINT(1) DEFAULT 0,
        latitude DECIMAL(10,8) NOT NULL,
        longitude DECIMAL(11,8) NOT NULL
    );
    """

    route_table_query = """
    CREATE TABLE IF NOT EXISTS Routes (
        route_id INT PRIMARY KEY AUTO_INCREMENT,
        poi_id_a INT NOT NULL,
        poi_id_b INT NOT NULL,
        distance_m DECIMAL(10,2) NOT NULL,
        travel_time_min DECIMAL(10,2) NOT NULL,
        is_accessible TINYINT(1) DEFAULT 0,
        FOREIGN KEY (poi_id_a) REFERENCES POIs(poi_id),
        FOREIGN KEY (poi_id_b) REFERENCES POIs(poi_id)
    );
    """
    history_table_query = """
    CREATE TABLE IF NOT EXISTS searchhistory (
        history_id INT PRIMARY KEY AUTO_INCREMENT,
        start_poi_id INT NOT NULL,
        end_poi_id INT NOT NULL,
        search_time DATETIME DEFAULT CURRENT_TIMESTAMP,
        distance_m DECIMAL(10,2),
        travel_time_min DECIMAL(10,2),
        algorithm VARCHAR(50),
        is_accessible TINYINT(1) DEFAULT 0,
        FOREIGN KEY (start_poi_id) REFERENCES POIs(poi_id),
        FOREIGN KEY (end_poi_id) REFERENCES POIs(poi_id)
    );
    """
    execute_query(connection, poi_table_query)
    execute_query(connection, route_table_query)
    execute_query(connection, history_table_query)
    load_initial_data_from_json(connection)

    return True
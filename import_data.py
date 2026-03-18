import json
import os
import db_connector as db

# --- Configuration ---
JSON_FILE = 'campus_nodes_edges.json'


def import_all_data():
    """
    Reads the JSON file and imports all nodes (POIs) and edges (Routes)
    into the SQLite database.
    """
    if not os.path.exists(JSON_FILE):
        print(f"ERROR: JSON file not found: {JSON_FILE}")
        return

    conn = db.create_connection()
    if conn is None:
        print("ERROR: Could not establish database connection.")
        return

    print("Initializing database tables...")
    db.initialize_db(conn)

    # Delete existing data before import to prevent duplicates and clean up errors
    db.execute_query(conn, "DELETE FROM POIs")
    db.execute_query(conn, "DELETE FROM Routes")
    print("Existing data cleared.")

    try:
        with open(JSON_FILE, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"ERROR: Failed to read or parse JSON file: {e}")
        conn.close()
        return

    # 1. Import Nodes (POIs)
    print(f"Starting import of {len(data.get('nodes', []))} POI nodes...")
    pois_imported = 0
    poi_map = {}  # To map original ID to new SQL ID

    # Insert POIs and map their original IDs to new database IDs
    for node in data.get('nodes', []):
        name = node.get('name', '') or ''
        category = node.get('type', 'Unknown')
        lat = node.get('lat')
        lng = node.get('lng')
        accessible = node.get('accessible', False)
        original_id = node.get('id')

        # Skip rows with missing coordinates which would crash the import
        if lat is None or lng is None:
            print(f"Skipping node {original_id} due to missing coordinates.")
            continue

        # Use a transaction for performance
        query = """
        INSERT INTO POIs (name, category, is_accessible, latitude, longitude) 
        VALUES (?, ?, ?, ?, ?)
        """
        # Execute the insert directly without the db_connector wrapper for faster bulk insert
        try:
            cursor = conn.cursor()
            cursor.execute(query, (name, category, accessible, lat, lng))
            new_id = cursor.lastrowid
            poi_map[original_id] = new_id
            pois_imported += 1
        except db.sqlite3.Error as e:
            print(f"Database insertion error for POI {original_id}: {e}", file=sys.stderr)
            conn.rollback()  # Rollback on error

    conn.commit()
    print(f"Successfully imported {pois_imported} POIs.")

    # 2. Import Edges (Routes)
    print(f"Starting import of {len(data.get('edges', []))} route edges...")
    routes_imported = 0

    for edge in data.get('edges', []):
        original_from = edge.get('from')
        original_to = edge.get('to')
        distance = edge.get('distance')
        time = edge.get('time')
        accessible = edge.get('accessible', False)

        # Get the new database IDs using the map
        poi_id_a = poi_map.get(original_from)
        poi_id_b = poi_map.get(original_to)

        if poi_id_a and poi_id_b and distance is not None and time is not None:
            # Insert A -> B and B -> A for bi-directional graph
            query = """
            INSERT INTO Routes (poi_id_a, poi_id_b, distance_m, travel_time_min, is_accessible) 
            VALUES (?, ?, ?, ?, ?)
            """
            params = (poi_id_a, poi_id_b, distance, time, accessible)

            # Execute the insert directly for faster bulk insert
            try:
                cursor = conn.cursor()
                cursor.execute(query, params)
                routes_imported += 1
            except db.sqlite3.Error as e:
                # Note: Errors here might be due to duplicate edges or bad FK. Skip.
                pass

        else:
            # print(f"Skipping edge due to missing mapped ID or data: {edge}")
            pass  # Skip paths that reference nodes we couldn't map or skipped

    conn.commit()
    print(f"Successfully imported {routes_imported} routes.")
    conn.close()
    print("Data import complete.")


if __name__ == '__main__':
    import_all_data()
# navigation_algorithms.py

import heapq
import sys
import collections  # Needed for BFS queue
# Used to handle data types coming from the MySQL database connector (already in your code)
from decimal import Decimal

# Set a high number for initial distance in Dijkstra's
INF = float('inf')


# --- Graph Structure Functions ---

def build_graph(pois, routes):
    """
    Builds a complete graph structure from the POI nodes and Route edges data.
    """
    if not pois or not routes:
        print("WARNING: Cannot build graph. POIs or Routes data is missing.", file=sys.stderr)
        return None

    nodes = {}
    for poi in pois:
        poi_id = poi['poi_id']
        # Ensure lat/lng are cast to float
        nodes[poi_id] = {
            'lat': float(poi['latitude']),
            'lng': float(poi['longitude']),
            'accessible': bool(poi['is_accessible'])
        }

    adj = {poi_id: {} for poi_id in nodes.keys()}

    for route in routes:
        # Assuming the database query returns 'start_poi_id' and 'end_poi_id'
        # NOTE: If your DB connector returns 'poi_id_a' and 'poi_id_b', you must change these keys:
        id_a = route.get('start_poi_id') or route.get('poi_id_a')
        id_b = route.get('end_poi_id') or route.get('poi_id_b')

        if id_a is None or id_b is None:
            continue

        # CRITICAL FIX: Convert Decimal distance to float
        distance = float(route['distance_m'])
        travel_time = float(route.get('travel_time_min', distance / 1.4))  # Fallback if time is missing
        accessible = bool(route['is_accessible'])

        if id_a in nodes and id_b in nodes:
            # Add edge A -> B
            adj[id_a][id_b] = {'weight': distance, 'time': travel_time, 'accessible': accessible}
            # Add edge B -> A (Assuming paths are undirected for simplicity)
            adj[id_b][id_a] = {'weight': distance, 'time': travel_time, 'accessible': accessible}

    print(f"Graph built successfully in memory with {len(nodes)} nodes.")
    return {'nodes': nodes, 'adj': adj}


# ----------------------------------------------------
# --- 1. Pathfinding Algorithms ---
# ----------------------------------------------------

def dijkstra(graph, start_id, end_id, accessible_mode=False):
    """
    Calculates the shortest path using Dijkstra's algorithm (based on distance).
    Returns: previous_nodes map
    """
    nodes = graph['nodes']
    adj = graph['adj']
    start_id = int(start_id)
    end_id = int(end_id)

    if start_id not in nodes or end_id not in nodes:
        return None

    distance_map = {node: INF for node in nodes}
    distance_map[start_id] = 0.0
    previous_nodes = {}

    # Priority queue: (distance, node_id)
    priority_queue = [(0.0, start_id)]

    while priority_queue:
        current_distance, current_node = heapq.heappop(priority_queue)

        if current_distance > distance_map[current_node]:
            continue

        if current_node == end_id:
            break

        for neighbor, edge_data in adj[current_node].items():

            if accessible_mode and not edge_data['accessible']:
                continue

            weight = edge_data['weight']  # Use distance as weight for Dijkstra's
            new_distance = current_distance + weight

            if new_distance < distance_map[neighbor]:
                distance_map[neighbor] = new_distance
                previous_nodes[neighbor] = current_node
                heapq.heappush(priority_queue, (new_distance, neighbor))

    return previous_nodes


def bfs(graph, start_id, end_id, accessible_mode=False):
    """
    Calculates the path with the fewest steps (hops) using BFS.
    Returns: previous_nodes map
    """
    nodes = graph['nodes']
    adj = graph['adj']
    start_id = int(start_id)
    end_id = int(end_id)

    if start_id not in nodes or end_id not in nodes:
        return None

    # queue stores nodes to visit
    queue = collections.deque([start_id])
    # visited also acts as the previous_nodes map
    previous_nodes = {start_id: None}

    while queue:
        current_node = queue.popleft()

        if current_node == end_id:
            break

        for neighbor, edge_data in adj[current_node].items():

            if accessible_mode and not edge_data['accessible']:
                continue

            if neighbor not in previous_nodes:
                previous_nodes[neighbor] = current_node
                queue.append(neighbor)

    return previous_nodes


def dfs(graph, start_id, end_id, accessible_mode=False):
    """
    Finds a path using DFS (not guaranteed to be shortest or fastest).
    Returns: previous_nodes map
    """
    nodes = graph['nodes']
    adj = graph['adj']
    start_id = int(start_id)
    end_id = int(end_id)

    if start_id not in nodes or end_id not in nodes:
        return None

    # stack stores nodes to visit
    stack = [start_id]
    # visited also acts as the previous_nodes map
    previous_nodes = {start_id: None}

    while stack:
        current_node = stack.pop()

        if current_node == end_id:
            break

        # Iterate in reverse to mimic depth-first behavior with a standard list
        for neighbor, edge_data in adj[current_node].items():

            if accessible_mode and not edge_data['accessible']:
                continue

            if neighbor not in previous_nodes:
                previous_nodes[neighbor] = current_node
                stack.append(neighbor)

    return previous_nodes


# ----------------------------------------------------
# --- 2. Path Reconstruction ---
# ----------------------------------------------------

def reconstruct_path_and_calculate_metrics(graph, start_id, end_id, previous_nodes):
    """
    Reconstructs the path from the previous_nodes map and calculates total distance and time.
    """
    nodes = graph['nodes']
    adj = graph['adj']

    # 1. Reconstruct Path (Node IDs)
    path_node_ids = []
    current = end_id

    if end_id not in previous_nodes and end_id != start_id:
        return None, 0.0, 0.0  # No path found

    while current is not None:
        path_node_ids.append(current)
        current = previous_nodes.get(current)

    path_node_ids.reverse()

    # If the first node is not the start_id, no complete path was found
    if not path_node_ids or path_node_ids[0] != start_id:
        return None, 0.0, 0.0

    # 2. Calculate Metrics and Convert to Coordinates
    total_distance = 0.0
    total_time = 0.0
    path_coords = []

    # Get coordinates for the first node
    path_coords.append((nodes[start_id]['lat'], nodes[start_id]['lng']))

    # Iterate through the path to sum metrics and get coordinates
    for i in range(len(path_node_ids) - 1):
        id_a = path_node_ids[i]
        id_b = path_node_ids[i + 1]

        # Check if the edge exists (it should, but safety first)
        if id_b in adj[id_a]:
            edge = adj[id_a][id_b]
            total_distance += edge['weight']
            total_time += edge['time']

        # Get coordinates for the second node
        path_coords.append((nodes[id_b]['lat'], nodes[id_b]['lng']))

    return path_coords, total_distance, total_time


# ----------------------------------------------------
# --- 3. Main Dispatcher Function ---
# ----------------------------------------------------

def find_shortest_path(graph, start_id, end_id, algorithm='dijkstra', accessible_mode=False):
    """
    Calculates the path using the specified algorithm and formats the result.
    """
    if not graph:
        return {"path": None, "distance": 0.0, "message": "Graph data is not loaded."}

    try:
        start_id = int(start_id)
        end_id = int(end_id)
    except (ValueError, TypeError):
        return {"path": None, "distance": 0.0, "message": "Invalid POI ID format."}

    previous_nodes = None
    algorithm = algorithm.lower()

    if algorithm == 'dijkstra':
        previous_nodes = dijkstra(graph, start_id, end_id, accessible_mode)
    elif algorithm == 'bfs':
        previous_nodes = bfs(graph, start_id, end_id, accessible_mode)
    elif algorithm == 'dfs':
        previous_nodes = dfs(graph, start_id, end_id, accessible_mode)
    else:
        return {"path": None, "distance": 0.0, "message": f"Algorithm '{algorithm}' not supported."}

    if previous_nodes is None:
        return {"path": None, "distance": 0.0, "message": "Start or end POI not in graph."}

    # Reconstruct path and calculate distance/time based on the found path
    path_coords, distance, time = reconstruct_path_and_calculate_metrics(
        graph, start_id, end_id, previous_nodes
    )

    if path_coords:
        return {
            'distance': round(distance, 2),
            'travel_time_min': round(time, 2),
            'path': path_coords,
            'message': f"Path found using {algorithm.upper()}."
        }

    return {"path": None, "distance": 0.0, "message": f"No path found using {algorithm.upper()}."}
# shortest_path_finder.py (MOCK/PLACEHOLDER)

def find_route(start_id, end_id, algorithm, accessible):
    """Mocks the output of a route finding algorithm for demonstration."""

    # MOCK names for the output (These should be replaced with real logic later)
    start_name = "Admin Building (Mock)" if start_id == 100 else "Start Location"
    end_name = "Library (Mock)" if end_id == 200 else "End Location"

    # This structure must match what app_server.py and db_connector.py expect
    return {
        "success": True,
        "start_name": start_name,
        "end_name": end_name,
        "total_time": 450.5,  # Mock distance in meters
        "algorithm": algorithm,
        "path_coords": [
            # Mock coordinates for visualization
            {"lat": 33.882, "lng": -117.885},
            {"lat": 33.883, "lng": -117.884},
            {"lat": 33.884, "lng": -117.883},
            {"lat": 33.885, "lng": -117.882}
        ]
    }
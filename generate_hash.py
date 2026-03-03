from flask_bcrypt import Bcrypt
from flask import Flask
import sys

# --- CONFIGURATION ---
# Define the users and the desired passwords
USERS_TO_HASH = {
    # Admin User
    "anjali": "ADMIN",
    # Teacher User
    "teacher": "buttermilk",
    # Student User
    "student": "amul",
}
# ---------------------

# Setup Flask and Bcrypt (required for the function to work correctly)
app = Flask(__name__)
# The app_context is necessary when running Bcryptoutside of the main Flask run loop
with app.app_context():
    bcrypt = Bcrypt(app)

    print("\n--- BCrypt Hash Generator Output ---")
    print("ACTION: Copy the hashes below and paste them into app_server.py.")
    print("------------------------------------")

    for username, password in USERS_TO_HASH.items():
        # Generate the hash (cost factor 12 is the default for Flask-Bcrypt)
        new_hash = bcrypt.generate_password_hash(password.encode('utf-8')).decode('utf-8')

        print(f"\nUsername: '{username}'")
        print(f"Password: '{password}'")
        print(f"Generated Hash (Copy this for {username.upper()}_PASSWORD_HASH):")
        print(new_hash)

    print("\n------------------------------------")
    print("Process complete. Update app_server.py with the new hashes and restart your Flask server.")
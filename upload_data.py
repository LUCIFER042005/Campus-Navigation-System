import mysql.connector

# 1. YOUR LOCAL XAMPP DETAILS
local_db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="AVNS_qPSvenKC8cfSHh-2YiB",
    database="smart_campus_db"
)

# 2. YOUR CLOUD AIVEN DETAILS (From your screenshot)
cloud_db = mysql.connector.connect(
    host="mysql-1eedeb3b-campus1.i.aivencloud.com",
    port=15747,
    user="avnadmin",
    password="YOUR_AIVEN_PASSWORD_HERE",  # Click the EYE icon in Aiven to get this
    database="defaultdb"
)


def migrate():
    local_cursor = local_db.cursor()
    cloud_cursor = cloud_db.cursor()

    # Get all tables from your laptop
    local_cursor.execute("SHOW TABLES")
    tables = local_cursor.fetchall()

    for (table_name,) in tables:
        print(f"Moving table: {table_name}...")

        # Get data from local
        local_cursor.execute(f"SELECT * FROM {table_name}")
        rows = local_cursor.fetchall()

        if rows:
            # Prepare insert query
            placeholders = ", ".join(["%s"] * len(rows[0]))
            insert_query = f"INSERT INTO {table_name} VALUES ({placeholders})"

            # This part is a bit advanced, but it works!
            cloud_cursor.executemany(insert_query, rows)
            cloud_db.commit()

    print("DONE! Your data is now in the cloud.")


migrate()
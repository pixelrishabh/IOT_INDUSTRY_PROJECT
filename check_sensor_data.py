from database.db import get_connection

conn = get_connection()
cursor = conn.cursor()

cursor.execute("""
    SELECT device_type, sensor_data
    FROM telemetry
    ORDER BY id DESC
    LIMIT 1;
""")

result = cursor.fetchone()

print("\nLatest telemetry:")
print(result)

cursor.close()
conn.close()
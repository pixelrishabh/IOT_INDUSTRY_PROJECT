import psycopg2

from psycopg2.extras import Json


DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "energy_db",
    "user": "energy_user",
    "password": "energy_password"
}


def get_connection():
    """
    Create and return a PostgreSQL connection.
    """

    return psycopg2.connect(**DB_CONFIG)


def insert_telemetry(data):
    """
    Insert one telemetry message into PostgreSQL.
    """

    connection = get_connection()

    try:

        cursor = connection.cursor()

        query = """
            INSERT INTO telemetry (
                device_id,
                device_type,
                timestamp,
                fault,
                sensor_data
            )
            VALUES (%s, %s, %s, %s, %s)
        """

        cursor.execute(
            query,
            (
                data["device_id"],
                data["device_type"],
                data["timestamp"],
                data.get("fault"),
                Json(data)
            )
        )

        connection.commit()

        cursor.close()

    except Exception as e:

        connection.rollback()

        print(f"❌ Database insert error: {e}")

    finally:

        connection.close()
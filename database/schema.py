from database.db import get_connection


def create_tables():

    connection = get_connection()

    try:

        cursor = connection.cursor()

        query = """
        CREATE TABLE IF NOT EXISTS telemetry (
            id BIGSERIAL PRIMARY KEY,

            device_id VARCHAR(100) NOT NULL,

            device_type VARCHAR(50) NOT NULL,

            timestamp TIMESTAMP NOT NULL,

            fault VARCHAR(100),

            sensor_data JSONB NOT NULL
        );
        """

        cursor.execute(query)

        connection.commit()

        print("✅ Telemetry table ready")

        cursor.close()

    except Exception as e:

        connection.rollback()

        print(f"❌ Table creation error: {e}")

    finally:

        connection.close()


if __name__ == "__main__":
    create_tables()
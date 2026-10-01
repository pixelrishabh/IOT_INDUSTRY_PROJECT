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


def get_telemetry_stats():
    """
    Fetch high-level telemetry and fault statistics from PostgreSQL.
    """
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                COUNT(*),
                COUNT(fault),
                COUNT(DISTINCT device_id),
                MIN(timestamp),
                MAX(timestamp),
                COUNT(CASE WHEN sensor_data ->> 'diagnosis' IS NOT NULL THEN 1 END)
            FROM telemetry
        """)
        row = cur.fetchone()
        cur.close()
        
        return {
            "total_records": int(row[0]) if row and row[0] is not None else 0,
            "total_faults": int(row[1]) if row and row[1] is not None else 0,
            "total_wells": int(row[2]) if row and row[2] is not None else 0,
            "first_timestamp": str(row[3]) if row and row[3] is not None else "N/A",
            "last_timestamp": str(row[4]) if row and row[4] is not None else "N/A",
            "total_diagnoses": int(row[5]) if row and row[5] is not None else 0
        }
    except Exception as e:
        print(f"⚠️ get_telemetry_stats error: {e}")
        return {
            "total_records": 0, "total_faults": 0, "total_wells": 0,
            "first_timestamp": "N/A", "last_timestamp": "N/A", "total_diagnoses": 0
        }
    finally:
        if conn:
            conn.close()


def get_distinct_well_ids():
    """
    Fetch list of distinct monitored well IDs.
    """
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT device_id FROM telemetry ORDER BY device_id ASC")
        rows = cur.fetchall()
        cur.close()
        return [r[0] for r in rows if r[0]]
    except Exception as e:
        print(f"⚠️ get_distinct_well_ids error: {e}")
        return []
    finally:
        if conn:
            conn.close()


def get_recent_telemetry_rows(limit: int = 500, well_id: str = None, faults_only: bool = False):
    """
    Fetch recent telemetry records with optional well filtering.
    """
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        clauses = []
        params = []
        if well_id:
            clauses.append("device_id = %s")
            params.append(well_id)
        if faults_only:
            clauses.append("fault IS NOT NULL")
            
        where_sql = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        query = f"""
            SELECT id, device_id, device_type, timestamp, fault, sensor_data
            FROM telemetry
            {where_sql}
            ORDER BY timestamp DESC
            LIMIT %s
        """
        params.append(limit)
        
        cur.execute(query, tuple(params))
        rows = cur.fetchall()
        col_names = [desc[0] for desc in cur.description]
        cur.close()
        
        return [dict(zip(col_names, r)) for r in rows]
    except Exception as e:
        print(f"⚠️ get_recent_telemetry_rows error: {e}")
        return []
    finally:
        if conn:
            conn.close()


def get_recent_incidents(limit: int = 50, well_id: str = None):
    """
    Fetch latest fault incidents from PostgreSQL.
    """
    return get_recent_telemetry_rows(limit=limit, well_id=well_id, faults_only=True)


def get_latest_anomaly_record(well_id: str = None):
    """
    Fetch the most recent anomaly/fault record from PostgreSQL for zero-click Overview loading.
    """
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        if well_id:
            query = """
                SELECT id, device_id, device_type, timestamp, fault, sensor_data
                FROM telemetry
                WHERE fault IS NOT NULL AND device_id = %s
                ORDER BY timestamp DESC
                LIMIT 1
            """
            cur.execute(query, (well_id,))
            row = cur.fetchone()
        else:
            # First try Petrobras WELL assets
            query = """
                SELECT id, device_id, device_type, timestamp, fault, sensor_data
                FROM telemetry
                WHERE fault IS NOT NULL AND device_id LIKE 'WELL%'
                ORDER BY timestamp DESC
                LIMIT 1
            """
            cur.execute(query)
            row = cur.fetchone()
            if not row:
                # Fallback to any fault record
                query = """
                    SELECT id, device_id, device_type, timestamp, fault, sensor_data
                    FROM telemetry
                    WHERE fault IS NOT NULL
                    ORDER BY timestamp DESC
                    LIMIT 1
                """
                cur.execute(query)
                row = cur.fetchone()
                
            if not row:
                # If no fault at all, return latest telemetry
                query = """
                    SELECT id, device_id, device_type, timestamp, fault, sensor_data
                    FROM telemetry
                    ORDER BY timestamp DESC
                    LIMIT 1
                """
                cur.execute(query)
                row = cur.fetchone()

        if row:
            col_names = [desc[0] for desc in cur.description]
            cur.close()
            return dict(zip(col_names, row))
        cur.close()
        return None
    except Exception as e:
        print(f"⚠️ get_latest_anomaly_record error: {e}")
        return None
    finally:
        if conn:
            conn.close()

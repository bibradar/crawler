import os
import requests
import psycopg2
from psycopg2.extras import execute_batch
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

# Database connection details from .env file
DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT", 5432)),  # Default to 5432 if DB_PORT is not set
}

# URL to crawl
URL = "http://graphite-kom.srv.lrz.de/render/?from=-60min&target=ap.apa{01,02,03,04,05,06,07,08,09,10,11,12,13}*-?mg*.ssid.*&format=json"

def fetch_data(url):
    """Fetch JSON data from the given URL."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return []

def parse_target(target):
    """Parse target string to extract access point name."""
    # Example target: "ap.apa01-0mg.ssid.@BayernWLAN"
    parts = target.split(".")
    access_point_name = parts[1]  # "apa01-0mg"
    ssid = parts[-1]             # "@BayernWLAN"
    return access_point_name, ssid

def unix_to_pg_timestamp(unix_time):
    """Convert Unix timestamp to a PostgreSQL-compatible timestamp."""
    return datetime.utcfromtimestamp(unix_time).isoformat()


def write_to_db(data):
    """Write the crawled data to the database."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # Insert or get AccessPoint
        access_point_query = """
        INSERT INTO AccessPoint (name, library_id) VALUES (%s, %s)
        ON CONFLICT (name) DO NOTHING
        RETURNING id;
        """

        # Insert Utilization data
        utilization_query = """
        INSERT INTO Utilization (accesspoint_id, timestamp, user_count)
        VALUES (%s, %s, %s)
        ON CONFLICT (accesspoint_id, timestamp) DO UPDATE
        SET user_count = EXCLUDED.user_count;
        """

        for entry in data:
            target = entry["target"]
            datapoints = entry["datapoints"]
            print(f"Processing data for target: {target}")

            # Parse target to extract AccessPoint name and SSID
            access_point_name, _ = parse_target(target)

            # Insert or retrieve AccessPoint ID
            cur.execute(access_point_query, (access_point_name, 1))
            access_point_id = cur.fetchone()
            if not access_point_id:
                cur.execute("SELECT id FROM AccessPoint WHERE name = %s", (access_point_name,))
                access_point_id = cur.fetchone()[0]

            # Prepare data for batch insertion into Utilization
            utilization_data = [
                (access_point_id, unix_to_pg_timestamp(dp[1]), dp[0] or 0)  # (accesspoint_id, timestamp, user_count)
                for dp in datapoints
                if dp[1] is not None
            ]
            execute_batch(cur, utilization_query, utilization_data)

        conn.commit()
        print("Data successfully written to the database.")
    except Exception as e:
        print(f"Error writing to database: {e}")
    finally:
        if conn:
            conn.close()

def main():
    """Main function."""
    print("Fetching data...")
    data = fetch_data(URL)

    if data:
        print("Writing data to database...")
        write_to_db(data)
    else:
        print("No data to write.")

if __name__ == "__main__":
    main()

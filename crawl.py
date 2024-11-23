import os, json
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
    "port": int(os.getenv("DB_PORT", 5432)),
}

# URL to crawl
URL = "http://graphite-kom.srv.lrz.de/render/?from=-1w&target=ap.apa{01,02,03,04,05,06,07,08,09,10,11,12,13}*-?gh*.ssid.*&format=json"

TIMEZONE = datetime.now().astimezone().tzinfo


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
    ssid = parts[-1]  # "@BayernWLAN"
    return access_point_name, ssid


def unix_to_pg_timestamp(unix_time):
    """Convert Unix timestamp to a PostgreSQL-compatible timestamp."""
    return datetime.fromtimestamp(unix_time, TIMEZONE).isoformat()


def write_to_db(cur, data, library_id):
    """Write the crawled data to the database."""

    ap_aggregated_datapoints = {}

    for entry in data:
        target = entry["target"]
        datapoints = entry["datapoints"]

        # Parse target to extract AccessPoint name and SSID
        access_point_name, ssid = parse_target(target)

        if access_point_name not in ap_aggregated_datapoints:
            ap_aggregated_datapoints[access_point_name] = {}

        for dp in datapoints:
            value, timestamp = dp
            if value is None:
                value = 0
            if timestamp is not None:
                if timestamp not in ap_aggregated_datapoints[access_point_name]:
                    ap_aggregated_datapoints[access_point_name][timestamp] = 0
                ap_aggregated_datapoints[access_point_name][timestamp] += value

        print(f"Aggregated data for {access_point_name} on ssid {ssid}")

    # print(ap_aggregated_datapoints)

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

    for access_point_name, datapoints in ap_aggregated_datapoints.items():
        print(f"Processing data for ap: {access_point_name}")

        # Insert or retrieve AccessPoint ID
        cur.execute(access_point_query, (access_point_name, library_id))
        access_point_id = cur.fetchone()
        if not access_point_id:
            cur.execute(
                "SELECT id FROM AccessPoint WHERE name = %s", (access_point_name,)
            )
            access_point_id = cur.fetchone()[0]

        # print(f"AccessPoint ID: {access_point_id}, datapoints: {datapoints}")

        # Prepare data for batch insertion into Utilization
        utilization_data = [
            (
                access_point_id,
                unix_to_pg_timestamp(timestamp),
                count,
            )  # (accesspoint_id, timestamp, user_count)
            for timestamp, count in datapoints.items()
            if timestamp is not None
        ]

        # for i in utilization_data:
        #    print(i)

        # print(
        #   f"Writing {len(utilization_data)} records to the database.",
        #   utilization_data,
        # )
        execute_batch(cur, utilization_query, utilization_data)

    print("Data successfully written to the database.")


def get_aps_of_bib(bib):
    aps = []
    for _, room in bib["rooms"].items():
        for ap in room["aps"]:
            aps.append(ap["name"])
    return aps


def fetch_bib(conn, cur, bib):
    aps = get_aps_of_bib(bib)
    url = f"http://graphite-kom.srv.lrz.de/render/?from=-2y&target=ap.{{{','.join(aps)}}}.ssid.*&format=json"
    # print(f"Fetching data for {bib['bib']} from {url}")

    # write to db
    library_query = """
    INSERT INTO Library (name, bib, uni, location)
    VALUES (%s, %s, %s, %s)
    ON CONFLICT (name) DO NOTHING
    RETURNING id;
    """

    data = (bib["name"], bib["bib"], bib["uni"], "\n".join(bib["address"]))
    cur.execute(library_query, data)
    library_id = cur.fetchone()

    if not library_id:
        cur.execute("SELECT id FROM Library WHERE bib = %s", (bib["bib"],))
        library_id = cur.fetchone()[0]

    print("Fetching data...")
    data = fetch_data(url)

    print(f"Received data for {len(data)} targets.")

    if data:
        print("Writing data to database...")
        write_to_db(cur, data, library_id)
        conn.commit()
    else:
        print("No data to write.")


def main():
    """Main function."""
    print("Reading in bibs.jons")
    with open("meta/bibs.json", "r") as f:
        bibs = json.loads(f.read())

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        for _, bib in bibs.items():
            print(f"Fetching data for {bib["bib"]}")
            fetch_bib(conn, cur, bib)
    except Exception as e:
        print(f"Error writing to database: {e}")
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    main()

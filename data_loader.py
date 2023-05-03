import pyarrow.parquet as pq
import pandas as pd
from neo4j import GraphDatabase
import time
import csv
from datetime import datetime


class DataLoader:

    def __init__(self, uri, user, password):
        """
        Connect to the Neo4j database and other init steps
        
        Args:
            uri (str): URI of the Neo4j database
            user (str): Username of the Neo4j database
            password (str): Password of the Neo4j database
        """
        self.driver = GraphDatabase.driver(uri, auth=(user, password), encrypted=False)
        self.driver.verify_connectivity()


    def close(self):
        """
        Close the connection to the Neo4j database
        """
        self.driver.close()


    # Define a function to create nodes and relationships in the graph
    def load_transform_file(self, file_path):
        """
        Load the parquet file and transform it into a csv file
        Then load the csv file into neo4j

        Args:
            file_path (str): Path to the parquet file to be loaded
        """

        # Read the parquet file
        trips = pq.read_table(file_path)
        trips = trips.to_pandas()

        # Some data cleaning and filtering
        trips = trips[['tpep_pickup_datetime', 'tpep_dropoff_datetime', 'PULocationID', 'DOLocationID', 'trip_distance', 'fare_amount']]

        # Filter out trips that are not in bronx
        bronx = [3, 18, 20, 31, 32, 46, 47, 51, 58, 59, 60, 69, 78, 81, 94, 119, 126, 136, 147, 159, 167, 168, 169, 174, 182, 183, 184, 185, 199, 200, 208, 212, 213, 220, 235, 240, 241, 242, 247, 248, 250, 254, 259]
        trips = trips[trips.iloc[:, 2].isin(bronx) & trips.iloc[:, 3].isin(bronx)]
        trips = trips[trips['trip_distance'] > 0.1]
        trips = trips[trips['fare_amount'] > 2.5]

        # Convert date-time columns to supported format
        trips['tpep_pickup_datetime'] = pd.to_datetime(trips['tpep_pickup_datetime'], format='%Y-%m-%d %H:%M:%S')
        trips['tpep_dropoff_datetime'] = pd.to_datetime(trips['tpep_dropoff_datetime'], format='%Y-%m-%d %H:%M:%S')

        # Convert to csv and store in the current directory
        save_loc = "/var/lib/neo4j/import/" + file_path.split(".")[0] + '.csv'
        trips.to_csv(save_loc, index=False)

        # TODO: Your code here
        session = self.driver.session()
        with open(save_loc, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # create nodes
                query1 = 'MERGE (p:Location {name: $pickup_id}) RETURN p'
                query2 = 'MERGE (d:Location {name: $dropoff_id}) RETURN d'
                session.run(query1, pickup_id= int(row['PULocationID']))
                session.run(query2, dropoff_id= int(row['DOLocationID']))

                # create relationship with remaining columns
                query3 = '''
                MATCH (p:Location {name: $pickup_id})
                MATCH (d:Location {name: $dropoff_id})
                MERGE (p)-[r:TRIP {distance: $distance, fare: $fare, pickup_dt: datetime($pickup_time), dropoff_dt: datetime($dropoff_time})]->(d)
                '''
                # session.run(query3, pickup_id=int(row['PULocationID']), dropoff_id=int(row['DOLocationID']), distance=float(row['trip_distance']), fare=float(row['fare_amount']), pickup_time=datetime.strptime(row['tpep_pickup_datetime'], '%Y-%m-%dT%H:%M:%S'), dropoff_time=datetime.strptime(row['tpep_dropoff_datetime'], '%Y-%m-%dT%H:%M:%S'))
                session.run(query3, pickup_id=int(row['PULocationID']), dropoff_id=int(row['DOLocationID']), distance=float(row['trip_distance']), fare=float(row['fare_amount']), pickup_time=datetime.strptime(row['tpep_pickup_datetime'], '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%dT%H:%M:%S'), dropoff_time=datetime.strptime(row['tpep_dropoff_datetime'], '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%dT%H:%M:%S'))


def main():

    total_attempts = 10
    attempt = 0

    # The database takes some time to starup!
    # Try to connect to the database 10 times
    while attempt < total_attempts:
        try:
            data_loader = DataLoader("neo4j://localhost:7687", "neo4j", "project2phase1")
            data_loader.load_transform_file("yellow_tripdata_2022-03.parquet")
            data_loader.close()

            attempt = total_attempts

        except Exception as e:
            print(f"(Attempt {attempt+1}/{total_attempts}) Error: ", e)
            attempt += 1
            time.sleep(10)


if __name__ == "__main__":
    main()

datetime(
  apoc.date.format(apoc.date.parse(datetimeString, 's', 'yyyy-MM-dd HH:mm:ss'), 'yyyy-MM-dd\'T\'HH:mm:ss'))
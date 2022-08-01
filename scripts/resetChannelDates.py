from datetime import datetime

from pymongo import MongoClient

# Initialize global variables
mongoClient = None
dbCollection = None
# --

def connectDb():
    print("Connecting to database")

    with open('../credentials/mongo-connection-string.txt') as connectionStringFile:
        connectionString = connectionStringFile.read()

        global mongoClient
        mongoClient = MongoClient(connectionString)

        db = mongoClient.get_default_database()
        global dbCollection
        dbCollection = db["channels"]

    print("Database connected")
    print("")


def disconnectDb():
    mongoClient.close()


def saveLastUpdates(date):
    result = dbCollection.update_many(
        filter={},
        update={"$set": {
            "lastUpdate": date,
            }})

    print(f"Updated {result.modified_count} documents.")


if __name__ == "__main__":
    connectDb()
    saveLastUpdates(datetime(2020, 8, 13))  # Last date where the original YouTube email notification were active
    disconnectDb()

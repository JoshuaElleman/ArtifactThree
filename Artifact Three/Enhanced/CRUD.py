from pymongo import MongoClient
from bson.objectid import ObjectId
import os


class BoardGamePlays(object):
    """CRUD operations for Board Game Plays in MongoDB"""

    def __init__(self):
        mongo_uri = os.getenv("MONGO_URI", "mongodb://mongo:27017/")
        mongo_db = os.getenv("MONGO_DB", "BoardGamePlays")
        mongo_collection = os.getenv("MONGO_COLLECTION", "Plays")

        self.client = MongoClient(mongo_uri)
        self.database = self.client[mongo_db]
        self.collection = self.database[mongo_collection]

    # Creates an entry in the connected database and collection. Passes data as
    # an entry to pymongo db.col.insert_one(). Returns True if creations is 
    # successful and False on failure.
    def create(self, data):
        try:
            result = self.collection.insert_one(data)
            return True if result.inserted_id else False
        except Exception as e:
            print(f"Error inserting document: {e}")
            return False

    # Reads data from the connected database and collection. Passes data as an
    # entry to pymongo db.col.find(). Returns list of elements from found 
    # entries, or if nothing is found or an error occurs and empty list.
    def read(self, data):
        try:
            cursor = self.collection.find(data)
            return list(cursor)
        except Exception as e:
            print(f"Error querying documents: {e}")
            return []

    # Updates entries from the connected database and collection. Passes query 
    # as the search parameter for the update and new_data as the updated element
    # of the entries. Returns the count of modified entries.
    def update(self, query, new_data):
        try:
            result = self.collection.update_many(query, {'$set': new_data})
            return result.modified_count
        except Exception as e:
            print(f"An error occurred: {e}")
            return 0

    # Deletes a single entry from the database, based on the record id provided
    def delete_one_by_id(self, record_id):
        try:
            result = self.collection.delete_one({"_id": ObjectId(record_id)})
            return result.deleted_count
        except Exception as e:
            print(f"An error occurred during delete: {e}")
            return 0

from pymongo import MongoClient


class AnimalShelter(object):
    """CRUD operations for Animal collection in MongoDB"""

    def __init__(self, username, password, host, port, database, collection):
        #
        # Initialize Connection
        #
        self.client = MongoClient("mongodb://%s:%s@%s:%d" % (username, password, host, port))
        self.database = self.client["%s" % (database)]
        self.collection = self.database["%s" % (collection)]

    # Creates an entry in the connected database and collection. Passes data as
    # an entry to pymongo db.col.insert_one(). Returns True if creations is 
    # succesful and False on failure.
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
    
    # Deletes entries from the connected database and collection. Passes query 
    # as the search parameter for the deletion. Returns the count of deleted 
    # entries.
    def delete(self, query):
      try:
        result = self.collection.delete_many(query)
        return result.deleted_count
      except Exception as e:
        print (f"An error occurred: {e}")
        return 0

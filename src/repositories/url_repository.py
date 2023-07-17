import logging
from datetime import datetime

from pymongo import MongoClient, UpdateOne


class UrlRepository:
    def __init__(self):
        mongo_client = MongoClient('mongodb://mongodb:27017/')
        mongo_db = mongo_client['crawler_db']
        self.collection = mongo_db['urls']
        try:
            self.collection.create_index([('url', 1)], unique=True)
        except Exception as e:
            pass

    def upsert_url(self, url, content):
        update_query = {
            '$set': {
                'content': content,
                'last_modified': datetime.now()
            }
        }
        upset_url = UpdateOne({'url': url}, update_query, upsert=True)
        self.collection.bulk_write([upset_url])

    def find_url(self, url):
        query = {'url': url}
        return self.collection.find_one(query)

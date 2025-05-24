# D:\ProductBox\inovient\Morpheus-v2\core\database.py
from pymongo import MongoClient
import os

DATABASE_URI = os.getenv("DATABASE_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME")

client = MongoClient(DATABASE_URI)
db = client[DATABASE_NAME]

conversations = db["conversations"]
user_collection = db["users"]
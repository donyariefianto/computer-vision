from motor.motor_asyncio import AsyncIOMotorClient
import os
from bson import ObjectId
from typing import List

MONGO_URI = os.getenv("MONGO_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME")

class MongoDBClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.client = AsyncIOMotorClient(MONGO_URI)
            cls._instance.db = cls._instance.client[DATABASE_NAME]
        return cls._instance

    def get_database(self):
        return self.db
    
# 📦 MongoDB Manager Class
class MongoDBManager:
    def __init__(self):
        """
        Initializes MongoDB connection.
        """
        self.client = AsyncIOMotorClient(MONGO_URI)
        self.db = MongoDBClient().get_database()
        self.collection = self.db["data"]

    async def insert(self, data: dict) -> str:
        """
        Inserts a document into MongoDB.
        """
        result = await self.collection.insert_one(data)
        return str(result.inserted_id)

    async def find_all(self, user_id: str, skip: int, limit: int) -> List[dict]:
        """
        Fetches all documents for a user with pagination.
        """
        cursor = self.collection.find({"user_id": user_id}).skip(skip).limit(limit)
        return [{**doc, "_id": str(doc["_id"])} async for doc in cursor]

    async def find_one(self, item_id: str, user_id: str) -> dict:
        """
        Fetches a single document by ID.
        """
        document = await self.collection.find_one({"_id": ObjectId(item_id), "user_id": user_id})
        if document:
            document["_id"] = str(document["_id"])
            return document
        return None

    async def update(self, item_id: str, user_id: str, update_data: dict) -> bool:
        """
        Updates a document in MongoDB.
        """
        result = await self.collection.update_one({"_id": ObjectId(item_id), "user_id": user_id}, {"$set": update_data})
        return result.modified_count > 0

    async def delete(self, item_id: str, user_id: str) -> bool:
        """
        Deletes a document from MongoDB.
        """
        result = await self.collection.delete_one({"_id": ObjectId(item_id), "user_id": user_id})
        return result.deleted_count > 0
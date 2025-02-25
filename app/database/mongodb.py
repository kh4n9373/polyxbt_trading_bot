from pymongo import errors, MongoClient
from app.config import settings
from motor.motor_asyncio import AsyncIOMotorClient


class MongoManager:
    __instances = {}

    def __new__(cls, db, uri=None):
        key = (db, uri)
        if key not in cls.__instances:
            cls.__instances[key] = super().__new__(cls)
            cls.__instances[key].__initialized = False
        return cls.__instances[key]

    def __init__(self, db, uri=None):
        if self.__initialized:
            return
        self.__initialized = True

        self.db = db
        self.connection_str = uri if uri is not None else settings.mongo_distilled_connection
        self.__client = MongoClient(self.connection_str)
        self.__database = self.__client[self.db]

    def insert_one(self, collection_name, data):
        collection = self.__database[collection_name]
        collection.insert_one(data)

    def insert_many(self, collection_name, data, ordered=False):
        collection = self.__database[collection_name]
        inserted_ids = []
        hash_ids = []
        error_ids = []

        try:
            collection.insert_many(data, ordered=ordered)
        except errors.OperationFailure as exc:
            write_errors = exc.details.get("writeErrors", [])

            if len(write_errors):
                error_ids = [error_doc["op"]["_id"] for error_doc in write_errors]
        finally:
            for doc in data:
                id = doc["_id"]
                hash_id = doc.get("hash_id", None)

                if id not in error_ids:
                    inserted_ids.append(id)

                    if hash_id:
                        hash_ids.append(hash_id)

        return inserted_ids, error_ids, hash_ids

    def upsert_many(self, collection_name, data):
        collection = self.__database[collection_name]
        return collection.bulk_write(data, ordered=False)

    def update_one(self, collection_name, filter, data, upsert=True):
        collection = self.__database[collection_name]
        collection.update_one(filter, data, upsert)

    def update_many(self, collection_name, filter, data):
        collection = self.__database[collection_name]
        collection.update_many(filter, data)

    def delete_many(self, collection_name, filter={}):
        collection = self.__database[collection_name]
        collection.delete_many(filter)

    def find_one(
        self,
        collection_name,
        filter={},
        sort=None,
        projection=None,
    ):
        collection = self.__database[collection_name]
        if sort:
            return collection.find_one(
                filter=filter,
                sort=[sort],
                projection=projection,
            )

        return collection.find_one(
            filter=filter,
            projection=projection,
        )

    def find_one_and_update(
        self, collection_name, filter={}, update={}, projection=None, sort=None
    ):
        collection = self.__database[collection_name]
        if sort:
            return collection.find_one_and_update(
                filter=filter,
                update=update,
                sort=sort,
                projection=projection,
                return_document=True,
            )

        return collection.find_one_and_update(
            filter=filter, update=update, projection=projection
        )

    def find(
        self,
        collection_name,
        filter={},
        projection=None,
        sort=None,
        offset=0,
        limit=None,
    ):
        collection = self.__database[collection_name]
        result = collection.find(filter, projection)
        if sort:
            result = result.sort(*sort)
        if offset:
            result = result.skip(offset)
        if limit:
            result = result.limit(limit)
        return list(result)

    def aggregate(self, collection_name, pipeline=[]):
        collection = self.__database[collection_name]
        return collection.aggregate(pipeline)

    def distinct(self, collection_name, field, filter={}):
        collection = self.__database[collection_name]
        return collection.distinct(field, filter)


class AsyncMongoManager:
    __instances = {}

    def __new__(cls, db, uri=None):
        key = (db, uri)
        if key not in cls.__instances:
            cls.__instances[key] = super().__new__(cls)
            cls.__instances[key].__initialized = False
        return cls.__instances[key]

    def __init__(self, db, uri=None):
        if self.__initialized:
            return
        self.__initialized = True

        self.db = db
        self.connection_str = uri if uri is not None else settings.mongo_distilled_connection
        self.__client = AsyncIOMotorClient(self.connection_str)
        self.__database = self.__client[self.db]

    async def insert_one(self, collection_name, data):
        collection = self.__database[collection_name]
        await collection.insert_one(data)

    async def insert_many(self, collection_name, data, ordered=False):
        collection = self.__database[collection_name]
        inserted_ids = []
        hash_ids = []
        error_ids = []

        try:
            await collection.insert_many(data, ordered=ordered)
        except errors.OperationFailure as exc:
            write_errors = exc.details.get("writeErrors", [])

            if len(write_errors):
                error_ids = [error_doc["op"]["_id"] for error_doc in write_errors]
        finally:
            for doc in data:
                id = doc["_id"]
                hash_id = doc.get("hash_id", None)

                if id not in error_ids:
                    inserted_ids.append(id)

                    if hash_id:
                        hash_ids.append(hash_id)

        return inserted_ids, error_ids, hash_ids

    async def upsert_many(self, collection_name, data):
        collection = self.__database[collection_name]
        return await collection.bulk_write(data, ordered=False)

    async def update_one(self, collection_name, filter, data, upsert=True):
        collection = self.__database[collection_name]
        await collection.update_one(filter, data, upsert=upsert)

    async def update_many(self, collection_name, filter, data):
        collection = self.__database[collection_name]
        await collection.update_many(filter, data)

    async def delete_many(self, collection_name, filter={}):
        collection = self.__database[collection_name]
        await collection.delete_many(filter)

    async def find_one(
        self,
        collection_name,
        filter={},
        sort=None,
        projection=None,
    ):
        collection = self.__database[collection_name]
        if sort:
            return await collection.find_one(
                filter=filter,
                sort=[sort],
                projection=projection,
            )

        return await collection.find_one(
            filter=filter,
            projection=projection,
        )

    async def find_one_and_update(
        self, collection_name, filter={}, update={}, projection=None, sort=None
    ):
        collection = self.__database[collection_name]
        if sort:
            return await collection.find_one_and_update(
                filter=filter,
                update=update,
                sort=sort,
                projection=projection,
                return_document=True,
            )

        return await collection.find_one_and_update(
            filter=filter, update=update, projection=projection
        )

    async def find(
        self,
        collection_name,
        filter={},
        projection=None,
        sort=None,
        offset=0,
        limit=None,
    ):
        collection = self.__database[collection_name]
        cursor = collection.find(filter, projection)
        if sort:
            cursor.sort(*sort)
        if offset:
            cursor.skip(offset)
        if limit:
            cursor.limit(limit)
        return [doc async for doc in cursor]

    async def aggregate(self, collection_name, pipeline=[]):
        collection = self.__database[collection_name]
        cursor = collection.aggregate(pipeline)
        return [doc async for doc in cursor]

    async def distinct(self, collection_name, field, filter={}):
        collection = self.__database[collection_name]
        return await collection.distinct(field, filter)

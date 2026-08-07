from pymongo import MongoClient

from config.settings import settings

_client = MongoClient(settings.mongo.uri)
_db = _client[settings.mongo.db_name]
_collection = _db[settings.mongo.assessments_collection]


def upsert_assessment(assessment_id: str, data: dict) -> None:
    _collection.update_one(
        {"assessment_id": assessment_id},
        {"$set": data},
        upsert=True,
    )


def get_assessment(assessment_id: str) -> dict | None:
    return _collection.find_one({"assessment_id": assessment_id}, {"_id": 0})
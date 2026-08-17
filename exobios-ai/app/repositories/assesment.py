from pymongo import MongoClient

from config.settings import settings

# Bounded connection/selection timeouts: without these, pymongo defaults to a
# 30s server-selection window, so a downed Mongo would stall every request
# that touches persistence (including /health/ready) for up to 30s before
# failing instead of failing fast.
_client = MongoClient(settings.mongo.uri, serverSelectionTimeoutMS=5000, connectTimeoutMS=5000)
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


def ping() -> None:
    """Raises on failure — used by the /health/ready check. Does not touch
    application data, just confirms the server is reachable and authenticated."""
    _client.admin.command("ping")
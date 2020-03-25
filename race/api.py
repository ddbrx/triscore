import re
from pymongo import MongoClient, ASCENDING, DESCENDING
from base import log


logger = log.setup_logger(__file__)


class RaceApi:
    def __init__(self, collection_name='races', dbname='triscore-test'):
        self.mongo_client = MongoClient()
        self.races_collection = self.mongo_client[dbname][collection_name]

    def get_races(self, starts_with='', ascending=True):
        where = {}
        if starts_with:
            rgx = re.compile(f"^/{starts_with}", re.IGNORECASE)
            where['RaceUrl'] = rgx

        return self._get_races(where=where, projection={'_id': 0}, sort=[('Date', ASCENDING if ascending else DESCENDING)])

    def _get_races(self, where={}, projection=None, sort=None):
        return self.races_collection.find(where, projection=projection, sort=sort)

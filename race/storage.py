import re
from pymongo import MongoClient, ASCENDING, DESCENDING
from base import log

logger = log.setup_logger(__file__)


class RaceStorage:
    def __init__(self, collection_name='races', dbname='triscore'):
        self.mongo_client = MongoClient()
        self.races_collection = self.mongo_client[dbname][collection_name]
        self._create_indices()

    def has_race(self, name):
        return self.races_collection.count_documents(filter={'name': name}) > 0

    def get_races(self, skip=0, limit=0, ascending=True):
        return self.races_collection.find(
            projection={'_id': 0},
            sort=[('date', ASCENDING if ascending else DESCENDING)]).skip(skip).limit(limit)

    def add_race(self, race_info, race_results):
        race = {**race_info}
        race['results'] = race_results
        return self.races_collection.insert_one(race)

    def _create_indices(self):
        self.races_collection.create_index('name', unique=True)
        self.races_collection.create_index([
            ('name', 'text'),
            ('location.d', 'text'),
            ('location.cy', 'text'),
            ('location.c', 'text')])

        self.races_collection.create_index('date')
        self.races_collection.create_index('brand')
        self.races_collection.create_index('type')

        self.races_collection.create_index('location.cy')
        self.races_collection.create_index('location.c')

        self.races_collection.create_index('distance.s.d')
        self.races_collection.create_index('distance.s.t')
        self.races_collection.create_index('distance.s.e')
        self.races_collection.create_index('distance.b.d')
        self.races_collection.create_index('distance.b.s')
        self.races_collection.create_index('distance.b.e')
        self.races_collection.create_index('distance.r.d')
        self.races_collection.create_index('distance.r.s')
        self.races_collection.create_index('distance.r.e')

        self.races_collection.create_index('stats.t')
        self.races_collection.create_index('stats.s')
        self.races_collection.create_index('stats.p')
        self.races_collection.create_index('stats.m')
        self.races_collection.create_index('stats.f')

import re
from pymongo import MongoClient, ASCENDING, DESCENDING
from base import log

logger = log.setup_logger(__file__)


MAX_RESULTS_LIMIT = 100


class RaceStorage:
    def __init__(self, collection_name='races', dbname='triscore'):
        self.mongo_client = MongoClient()
        self.races_collection = self.mongo_client[dbname][collection_name]
        self._create_indices()

    def has_race(self, name, date):
        return self.races_collection.count_documents(filter={'name': name, 'date': date}) > 0

    def get_top_races(self, name='', country='', sort_field='date', sort_order=DESCENDING, skip=0, limit=0):
        projection = {'_id': 0, 'results': 0}
        sort = [(sort_field, sort_order)]

        where = {}
        if country:
            where['location.c'] = country

        query = {}
        name = name.strip()
        if name:
            is_complex_filter = name.find(' ') != -1
            if is_complex_filter:
                # exact search
                name = f'\"{name}\"'

            text_query = {'$text': {'$search': name}}
            if len(where) > 0:
                query['$and'] = [
                    where,
                    text_query
                ]
            else:
                query = text_query
        else:
            query = where

        logger.info(f'query: \'{query}\'')
        return self.races_collection.find(
            query,
            sort=sort,
            projection=projection
        ).skip(skip).limit(limit)

    def get_races(self, skip=0, limit=0, ascending=True):
        return self.races_collection.find(
            projection={'_id': 0},
            sort=[('date', ASCENDING if ascending else DESCENDING)]).skip(skip).limit(limit)

    def get_race_results(self, name, date, sort_field, sort_order, skip=0, limit=0):
        query = [
            {
                '$match': {'name': name, 'date': date}
            },
            {
                '$unwind': '$results'
            },
            {
                '$sort': {sort_field: sort_order}
            },
            {
                '$skip': skip
            },
            {
                '$limit': limit
            },
            {
                '$project': {'_id': 0}
            }
        ]

        logger.info(f'get race results aggregate query: {query}')
        return self.races_collection.aggregate(query)

    def add_race(self, race_info, race_results):
        race = {**race_info}
        race['results'] = race_results
        return self.races_collection.insert_one(race)

    def _create_indices(self):
        self.races_collection.create_index(
            [('name', 1), ('date', -1)], unique=True)
        self.races_collection.create_index([
            ('name', 'text'),
            ('location.d', 'text'),
            ('location.cy', 'text'),
            ('location.c', 'text')])

        self.races_collection.create_index('date')
        self.races_collection.create_index('brand')
        self.races_collection.create_index('type')

        self.races_collection.create_index('location.d')
        self.races_collection.create_index('location.ct')
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

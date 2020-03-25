import argparse
import json
import os
from pymongo import MongoClient, ASCENDING, DESCENDING

from base import dt, log


logger = log.setup_logger(__file__)

NO_LIMIT = 1000 * 1000 * 1000


class ScoreApi:
    def __init__(self, collection_name='scores', dbname='triscore-test'):
        self.mongo_client = MongoClient()
        self.scores_collection = self.mongo_client[dbname][collection_name]
        self._create_indices()

    def get_top_athletes(self, name='', country='', sort_field='rating', sort_order=DESCENDING, skip=0, limit=0):
        projection = {'_id': 0, 'history': 0, 'prefixes': 0}
        sort = [(sort_field, sort_order), ('rating', sort_order)]

        where = {}
        if country:
            where['country'] = country

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

        logger.debug(f'query: \'{query}\'')
        return self.scores_collection.find(
            query,
            sort=sort,
            projection=projection
        ).skip(skip).limit(limit)

    def find_athlete(self, profile):
        where = {'profile': profile}
        projection = {'prefixes': 0, '_id': 0}
        return self.scores_collection.find_one(where, projection=projection)

    def get_athletes(self, profiles=[]):
        where = {}
        if len(profiles) > 0:
            where = {'profile': {'$in': profiles}}
        projection = {'prefixes': 0, '_id': 0}
        return self.scores_collection.find(where, projection=projection)

    def profile_exists(self, profile):
        return self.scores_collection.count({'profile': profile})

    def add_athlete(self, athlete):
        self.scores_collection.insert_one(athlete)

    def update_athlete(self, profile, race_summary, rating, races):
        self.scores_collection.update_one(
            {'profile': profile},
            {
                '$set': {'rating': rating, 'races': races},
                '$push': {'history': race_summary}
            }
        )

    def update_athlete_field(self, profile, field, value):
        self.scores_collection.update_one(
            {'profile': profile},
            {
                '$set': {field: value}
            }
        )

    def push_athlete_array_field(self, profile, field, single_value_or_list):
        value_clause = single_value_or_list
        if isinstance(single_value_or_list, list):
            value_clause = {'$each': single_value_or_list}
        self.scores_collection.update_one(
            {'profile': profile},
            {
                '$push': {field: value_clause}
            }
        )

    def _create_indices(self):
        self.scores_collection.create_index('profile', unique=True)
        self.scores_collection.create_index([('rating', DESCENDING)])
        self.scores_collection.create_index(
            [('races', DESCENDING), ('rating', DESCENDING)])
        self.scores_collection.create_index('name')
        self.scores_collection.create_index(
            [('country', DESCENDING), ('rating', DESCENDING)])
        self.scores_collection.create_index('gender')


class MockScoreApi:
    def __init__(self):
        self.athlete_by_profile = {}

    def get_athletes(self, profiles):
        athletes = []
        for profile in profiles:
            if profile in self.athlete_by_profile:
                athletes.append(self.athlete_by_profile[profile])
        return athletes

    def profile_exists(self, profile):
        return profile in self.athlete_by_profile

    def add_athlete(self, athlete):
        profile = athlete['profile']
        assert profile not in self.athlete_by_profile, f'duplicated profile: {profile}'
        self.athlete_by_profile[profile] = athlete

    def update_athlete(self, profile, race_summary, rating, races):
        assert profile in self.athlete_by_profile, f'profile not found: {profile}'

        self.athlete_by_profile[profile]['rating'] = rating
        self.athlete_by_profile[profile]['races'] = races
        self.athlete_by_profile[profile]['history'].append(race_summary)

    def get_top_athletes(self, limit=NO_LIMIT):
        return sorted(
            list(self.athlete_by_profile.values()), key=lambda item: -item['rating'])[0:limit]

import argparse
import json
import os
import re
from pymongo import MongoClient, ASCENDING, DESCENDING

from base import dt, log
from . import tristats_api


RACES_UPDATE_PERIOD_SEC = 86400 * 10
# RACES_UPDATE_PERIOD_SEC = 60
MAX_ATHLETES_LIMIT = 100 * 1000 * 1000

logger = log.setup_logger(__file__)


class MongoApi:
    def __init__(self, dbname='triscore-test'):
        self.mongo_client = MongoClient()
        self.db = self.mongo_client[dbname]
        self._create_mongo_indices()

    def get_races(self, ascending=True):
        self._update_races_if_needed()
        count = self.db.races.count()
        return self.db.races.find(sort=[('Date', ASCENDING if ascending else DESCENDING)]), count

    def get_races_json(self, ascending=True):
        return [race for race in self.get_races(ascending=ascending)]

    def get_results_json(self, race):
        return race['Results']

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

            query['$and'] = [
                {'$text': {'$search': name}},
                where
            ]
        else:
            query = where

        logger.debug(f'query: \'{query}\'')
        return self.db.scores.find(
            query,
            sort=sort,
            projection=projection
        ).skip(skip).limit(limit)

    def find_athlete(self, profile):
        where = {'profile': profile}
        projection = {'prefixes': 0, '_id': 0}
        return self.db.scores.find_one(where, projection=projection)

    def get_athletes(self, profiles=[]):
        where = {}
        if len(profiles) > 0:
            where = {'profile': {'$in': profiles}}
        projection = {'prefixes': 0, '_id': 0}
        return self.db.scores.find(where, projection=projection)

    def profile_exists(self, profile):
        return self.db.scores.count({'profile': profile})

    def add_athlete(self, athlete):
        self.db.scores.insert_one(athlete)

    def update_athlete(self, profile, race_summary, rating, races):
        self.db.scores.update_one(
            {'profile': profile},
            {
                '$set': {'rating': rating, 'races': races},
                '$push': {'history': race_summary}
            }
        )
        # self.db.scores.update_one(
        #     {'profile': profile}, {'$push': {'history': race_summary}})

    def update_athlete_field(self, profile, field, value):
        self.db.scores.update_one(
            {'profile': profile},
            {
                '$set': {field: value}
            }
        )

    def push_athlete_array_field(self, profile, field, single_value_or_list):
        value_clause = single_value_or_list
        if isinstance(single_value_or_list, list):
            value_clause = {'$each': single_value_or_list}
        self.db.scores.update_one(
            {'profile': profile},
            {
                '$push': {field: value_clause}
            }
        )

    def _update_races_if_needed(self):
        delta = dt.now() - self._get_last_races_update_dt()
        update_needed = delta.total_seconds() > RACES_UPDATE_PERIOD_SEC
        logger.info('{} since last update: update is {} needed'.format(
            delta, '' if update_needed else 'not'))

        if update_needed:
            added_count = self._update_races()
            self._add_meta_item(added_count)

    def _get_last_races_update_dt(self):
        last_races_update = self.db.meta.find_one(
            {'url': tristats_api.RACES_URL}, sort=[('date', DESCENDING)])
        return dt.datetime_from_string(
            last_races_update['datetime']) if last_races_update else dt.min

    def _update_races(self):
        logger.info('checking for new races')
        races_json = self._load_json(tristats_api.RACES_URL)
        added_count = 0
        for race in races_json:
            race_url = race['RaceUrl']
            if self.db.races.find_one({'RaceUrl': race_url}):
                break

            results_url = f"{tristats_api.RESULTS_URL}/{race_url}"
            results_json = self._load_json(results_url)
            race['Results'] = results_json

            logger.info(f'adding new race {race_url}')
            self.db.races.insert_one(race)
            added_count += 1
        logger.info(f'{added_count} new races added')
        return added_count

    def _add_meta_item(self, added_count):
        meta_item = {
            'url': tristats_api.RACES_URL,
            'datetime': dt.datetime_to_string(dt.now()),
            'added': added_count
        }
        self.db.meta.insert_one(meta_item)

    def _create_mongo_indices(self):
        self._create_race_indices()
        self._create_score_indices()

    def _create_race_indices(self):
        self.db.races.create_index('RaceUrl', unique=True)
        self.db.races.create_index([('Date', ASCENDING)])
        self.db.races.create_index('RaceCountry')

    def _create_score_indices(self):
        self.db.scores.create_index('profile', unique=True)
        self.db.scores.create_index([('rating', DESCENDING)])
        self.db.scores.create_index([('races', DESCENDING), ('rating', DESCENDING)])
        self.db.scores.create_index('name')
        self.db.scores.create_index([('country', DESCENDING), ('rating', DESCENDING)])
        self.db.scores.create_index('gender')

    def _load_json(self, url):
        text = tristats_api.load_url(url)
        return json.loads(text) if text else {}


class ReadOnlyApi:
    def __init__(self, dbname='triscore-test'):
        self.read_only_mongo_api = MongoApi(dbname)
        self.athlete_by_profile = {}

    def get_races(self, ascending=True):
        return self.read_only_mongo_api.get_races(ascending)

    def get_races_json(self, ascending=True):
        return self.read_only_mongo_api.get_races_json(ascending)

    def get_results_json(self, race):
        return self.read_only_mongo_api.get_results_json(race)

    def get_top_athletes(self, limit=MAX_ATHLETES_LIMIT):
        return sorted(
            list(self.athlete_by_profile.values()), key=lambda item: -item['rating'])[0:limit]

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

    def add_athlete_race_summary(self, profile, race_summary):
        assert profile in self.athlete_by_profile, f'profile not found: {profile}'
        new_rating = race_summary['rating_after']

        self.athlete_by_profile[profile]['rating'] = new_rating
        self.athlete_by_profile[profile]['races'] += 1
        self.athlete_by_profile[profile]['history'].append(race_summary)

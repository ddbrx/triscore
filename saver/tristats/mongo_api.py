import argparse
import json
import os

from pymongo import MongoClient, ASCENDING, DESCENDING

import dt
import log
import tristats_api


RACES_UPDATE_PERIOD_SEC = 86400 * 10
# RACES_UPDATE_PERIOD_SEC = 60

logger = log.setup_logger(__file__)


class MongoApi:
    def __init__(self, dbname='triscore-test'):
        self.mongo_client = MongoClient()
        self.db = self.mongo_client[dbname]
        self._create_mongo_indices()

    def get_races(self, ascending=True):
        self._update_races_if_needed()
        count = self.db.races.count()
        return (self.db.races.find(sort=[('Date', ASCENDING if ascending else DESCENDING)]), count)

    def get_races_json(self, ascending=True):
        races_json = []
        for race in self.get_races(ascending=ascending):
            races_json.append(race)
        return races_json

    def get_results_json(self, race):
        return race['Results']

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
        self.db.races.create_index('RaceUrl', unique=True)
        self.db.races.create_index('RaceCountry')
        self.db.races.create_index([('Date', ASCENDING)])

    def _load_json(self, url):
        text = tristats_api.load_url(url)
        return json.loads(text) if text else {}

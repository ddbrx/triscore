import argparse
import dt
import json
import log
import os
import tristats

from pymongo import MongoClient, ASCENDING, DESCENDING


RACES_UPDATE_PERIOD_SEC = 86400 * 10
# RACES_UPDATE_PERIOD_SEC = 60

logger = log.setup_logger(__name__)


class MongoApi:
    def __init__(self, dbname):
        self.mongo_client = MongoClient()
        self.db = self.mongo_client[dbname]
        self._create_mongo_indices()

    def get_races(self, acsending=True):
        self._add_new_races_if_needed()
        return self.db.races.find(sort=[('Date', ASCENDING if acsending else DESCENDING)])

    def _add_new_races_if_needed(self):
        current_dt = dt.now()
        last_races_update_dt = self._get_last_races_update_dt()
        delta = current_dt - last_races_update_dt
        if delta.total_seconds() > RACES_UPDATE_PERIOD_SEC:
            logger.info(
                f'last races update: {last_races_update_dt} delta: {delta}')
            self._add_new_races()

    def _get_last_races_update_dt(self):
        last_races_update = self.db.update_info.find_one(
            {'url': tristats.RACES_URL}, sort=[('date', DESCENDING)])
        return dt.datetime_from_string(
            last_races_update['datetime']) if last_races_update else dt.min

    def _add_new_races(self):
        races_json = self._load_json(tristats.RACES_URL)
        added_count = 0
        for race in races_json:
            race_url = race['RaceUrl']
            if self.db.races.find_one({'RaceUrl': race_url}):
                break

            results_url = f"{tristats.RESULTS_URL}{race_url}"
            results_json = self._load_json(results_url)
            race['Results'] = results_json

            logger.info(f'adding new race {race_url}')
            self.db.races.insert_one(race)
            added_count += 1

        logger.info(f'{added_count} new races added')
        update_info_item = {'url': tristats.RACES_URL, 'datetime': dt.datetime_to_string(
            dt.now()), 'added': added_count}
        self.db.update_info.insert_one(update_info_item)

    def _create_mongo_indices(self):
        self.db.races.create_index('RaceUrl', unique=True)
        self.db.races.create_index('RaceCountry')
        self.db.races.create_index([('Date', ASCENDING)])

    def _load_json(self, url):
        text = tristats.load_url(url)
        return json.loads(text) if text else {}

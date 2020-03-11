import argparse
import dt
import json
import log
import os
import tristats


RACES_UPDATE_PERIOD_SEC = 86400

logger = log.setup_logger(__name__)


class FsApi:
    def get_races_json(self, acsending=True):
        races_cache_file = self._get_races_cache_file()
        return self._load_json(tristats.RACES_URL, races_cache_file, reverse=acsending)

    def get_results_json(self, race_url, race_date):
        race_yyyymmdd = dt.datetime_to_string(
            dt.datetime_from_string(race_date), format='%Y-%m-%d')
        race_url_stripped = race_url.strip('/')
        results_cache_file = os.path.join(
            'data', 'results', race_url_stripped, f'{race_yyyymmdd}.json')
        results_url = f"{tristats.RESULTS_URL}/{race_url_stripped}"
        return self._load_json(results_url, results_cache_file)

    def _get_races_cache_file(self):
        current_dt = dt.now()
        last_races_update_dt = self._get_last_races_update_dt()
        delta_sec = (current_dt - last_races_update_dt).total_seconds()
        cache_dt = current_dt if delta_sec > RACES_UPDATE_PERIOD_SEC else last_races_update_dt

        return os.path.join(
            self._get_races_dir(), dt.datetime_to_string(cache_dt) + '.json')

    def _get_races_dir(self):
        return os.path.join('data', 'races')

    def _get_last_races_update_dt(self):
        races_dir = self._get_races_dir()
        max_dt = dt.min
        for race_file in os.listdir(races_dir):
            if race_file.endswith('.json'):
                max_dt = max(max_dt, dt.datetime_from_string(
                    os.path.splitext(race_file)[0]))
        return max_dt

    def _create_races_indices(self):
        race_collection = self.db.races
        race_collection.create_index('RaceUrl', unique=True)
        race_collection.create_index([('Date', ASCENDING)])

    def _load_json(self, url, cache_file, reverse=False):
        text = self._load_text(url, cache_file)
        if text:
            j = json.loads(text)
            if reverse:
                j.reverse()
            return j
        return {}

    def _load_text(self, url, cache_file):
        if not os.path.exists(cache_file) or os.stat(cache_file).st_size == 0:
            text = tristats.load_url(url)
            self._write_file(text, cache_file)
            return text

        return self._load_file(cache_file)

    def _write_file(self, text, file):
        logger.debug(f'writing to file: {file}')
        os.makedirs(os.path.dirname(file))
        with open(file, 'w') as f:
            f.write(text)

    def _load_file(self, file):
        logger.info(f'loading file: {file}')
        with open(file, 'r') as f:
            return f.read()

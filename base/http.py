import json
import os
import requests
import hashlib
from base import log, dt

logger = log.setup_logger(__file__)


class CachedUrl:
    CACHE_FILE_EXTENSION = '.cache'

    def __init__(self, url, headers, cache_dir, timeout=None):
        self.url = url
        self.headers = headers
        url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()
        self.cache_dir = os.path.join(cache_dir, url_hash)
        self.timeout = timeout
        self._create_dirs_if_needed(self.cache_dir)

    def get(self):
        cache_file = self._get_cache_file()
        if self._file_is_empty(cache_file):
            text = get(self.url, self.headers)
            self._write_file(text, cache_file)
            return text
        return self._read_file(cache_file)

    def _file_is_empty(self, file):
        return not os.path.exists(file) or os.stat(file).st_size == 0

    def _get_cache_file(self):
        cache_dt = self._get_cache_dt(dt.now())
        cache_filename = dt.datetime_to_string(cache_dt) + self.CACHE_FILE_EXTENSION
        return os.path.join(self.cache_dir, cache_filename)

    def _get_cache_dt(self, current_dt):
        last_update_dt = self._get_max_update_dt(
            self.cache_dir, endswith=self.CACHE_FILE_EXTENSION)
        if last_update_dt is None:
            return current_dt

        if self.timeout is None:
            return last_update_dt

        delta_sec = (current_dt - last_update_dt).total_seconds()
        if delta_sec > self.timeout:
            return current_dt

        return last_update_dt

    def _get_max_update_dt(self, dir, endswith):
        max_dt = dt.min
        for race_file in os.listdir(dir):
            if race_file.endswith(endswith):
                filename_dt = os.path.splitext(race_file)[0]
                max_dt = max(max_dt, dt.datetime_from_string(filename_dt))
        return max_dt if max_dt != dt.min else None

    def _create_dirs_if_needed(self, dir):
        os.makedirs(dir, exist_ok=True)

    def _read_file(self, file):
        logger.debug(f'loading from file: {file}')
        with open(file, 'r') as f:
            return f.read()

    def _write_file(self, text, file):
        logger.debug(f'writing to file: {file}')
        dir = os.path.dirname(file)
        with open(file, 'w') as f:
            f.write(text)


def get(url, headers):
    logger.debug(f'loading url {url} headers: {headers}')
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        logger.error(f'GET failed url: {url} code: {r.status_code}')
        return None
    return r.text


def get_json(url):
    text = get(url)
    return json.loads(text) if text else {}

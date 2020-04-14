import json
import os
from pathlib import Path
from pymongo import MongoClient, ASCENDING, DESCENDING

from base import log, http
from time import sleep

logger = log.setup_logger(__file__, debug=True)

SCRIPT_DIR = Path(__file__).parent


def empty_transformer(race):
    return race


def empty_filter(race):
    return False


class DataStorage:
    CACHE_NAME = '.cache'
    URL_FIELD = 'url'
    DATA_FIELD = 'data'
    PROCESSED_FIELD = 'processed'
    INVALID_FIELD = 'invalid'

    def __init__(self, collection_name, db_name='data', indices=[]):
        self.db_name = db_name
        self.collection_name = collection_name

        self.mongo_client = MongoClient()
        self.data_collection = self.mongo_client[db_name][collection_name]
        for index in indices:
            self.data_collection.create_index(index)

    def find(self, where={}, projection=None, sort=None, skip=0, limit=0):
        return self.data_collection.find(where, projection=projection, sort=sort).skip(skip).limit(limit)

    def find_one(self, where={}, projection=None, sort=None):
        return self.data_collection.find_one(where, projection=projection, sort=sort)

    def update(self,
               id_fields,
               list_url,
               list_update_frequency_sec,
               list_transformer=empty_transformer,
               list_filter=empty_filter,
               data_url_field=None,
               data_url_transformer=None,
               add_invalid=False,
               dry_run=True,
               limit=-1):

        cache_dir = Path(SCRIPT_DIR, self.CACHE_NAME, self.collection_name)
        cached_list = http.CachedUrl(
            url=list_url,
            cache_dir=cache_dir,
            timeout=list_update_frequency_sec)

        if len(id_fields) == 1:
            self.data_collection.create_index(id_fields[0], unique=True)
        else:
            indices = [(id_field, DESCENDING) for id_field in id_fields]
            self.data_collection.create_index(indices)

        logger.info(f'checking for new data')

        list_data = cached_list.get()
        list_json = list_transformer(json.loads(list_data))
        list_length = len(list_json)

        inserted_ids = []
        for i, item in enumerate(list_json):
            if i == limit:
                logger.info(f'stop by count limit: {limit}')
                break

            id_map = {id_field: item[id_field] for id_field in id_fields}
            logger.debug(f'{i + 1}/{list_length} {id_map}')

            if list_filter(item):
                logger.debug(f'filter item')
                continue

            if self.data_collection.find_one(id_map):
                logger.debug(f'skip existing item')
                continue

            if data_url_transformer:
                data_url = data_url_transformer(item)
                data_json = http.get_json(data_url)
                item[self.DATA_FIELD] = data_json[data_url_field] if data_url_field else data_json
                item[self.URL_FIELD] = data_url
                sleep(1)

            item[self.PROCESSED_FIELD] = False

            if add_invalid:
                item[self.INVALID_FIELD] = False

            if dry_run:
                logger.info(f'DRY RUN: item {data_id} inserted')
            else:
                insert_result = self.data_collection.insert_one(item)
                inserted_ids.append(str(insert_result.inserted_id))

        return inserted_ids

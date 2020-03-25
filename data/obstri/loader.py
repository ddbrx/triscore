#!/usr/bin/env python3
from base import log, utils
from data.storage import DataStorage
import url

logger = log.setup_logger(__file__)

UPDATE_FREQUENCY_SEC = 86400
# UPDATE_FREQUENCY_SEC = 60


def racesv2_transformer(races_list):
    return races_list['racesv2']


def main():
    storage = DataStorage(collection_name='obstri')
    updated_ids = storage.update(
        id_fields=['r', 'd'],
        list_url=url.RACES_URL,
        list_update_frequency_sec=UPDATE_FREQUENCY_SEC,
        list_transformer=racesv2_transformer,
        dry_run=False,
        limit=-1)
    logger.info(f'{len(updated_ids)} items updated')


if __name__ == '__main__':
    main()

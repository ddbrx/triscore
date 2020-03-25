#!/usr/bin/env python3
from base import log, utils
from data.storage import DataStorage
import parser
import url

logger = log.setup_logger(__file__)

UPDATE_FREQUENCY_SEC = 86400
# UPDATE_FREQUENCY_SEC = 60


def get_data_url(race):
    return url.get_results_url(parser.get_race_url(race))


def first_item_transformer(races_list):
    return races_list[0]


def ironman_filter(race):
    name = parser.get_race_name(race)
    return name.lower().find('ironman') == -1


def main():
    storage = DataStorage(collection_name='tristats')

    updated_ids = storage.update(
        id_fields=['RaceUrl'],
        list_url=url.TRISTATS_RACES_URL,
        list_update_frequency_sec=UPDATE_FREQUENCY_SEC,
        # list_filter=ironman_filter,
        data_url_transformer=get_data_url,
        dry_run=True,
        limit=100)
    logger.info(f'{len(updated_ids)} items updated')


if __name__ == '__main__':
    main()

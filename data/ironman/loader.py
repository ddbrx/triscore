#!/usr/bin/env python3
from base import log, utils
from data.storage import DataStorage
import parser
import url

logger = log.setup_logger(__file__)

UPDATE_FREQUENCY_SEC = 86400
# UPDATE_FREQUENCY_SEC = 60


def get_data_url(race):
    return url.get_results_url(parser.get_event_id(race))


def first_item_transformer(races_list):
    return races_list[0]


def ironman_filter(race):
    name = parser.get_event_name(race)
    return name.lower().find('ironman') == -1


def t5150_filter(race):
    name = parser.get_event_name(race)
    return name.lower().find('5150') == -1


def ironman_and_t5150_filter(race):
    return ironman_filter(race) and t5150_filter(race)


def main():
    storage = DataStorage(collection_name='ironman')
    updated_ids = storage.update(
        id_fields=['SubEventId'],
        list_url=url.RACES_URL,
        list_update_frequency_sec=UPDATE_FREQUENCY_SEC,
        list_transformer=first_item_transformer,
        list_filter=ironman_and_t5150_filter,
        data_url_field='data',
        data_url_transformer=get_data_url,
        dry_run=False,
        limit=4)
    logger.info(f'{len(updated_ids)} items updated')


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
from base import log, utils
from data.storage import DataStorage
import parser
import url

logger = log.setup_logger(__file__)

UPDATE_FREQUENCY_SEC = 86400
# UPDATE_FREQUENCY_SEC = 60


def ironman_filter(race):
    name = parser.get_event_name(race)
    return not name.lower().startswith('irm')


def list_transformer(events_list):
    return events_list['list']


def get_events_url(start=0, max=0):
    return f'{url.RTRT_EVENTS_URL}&start={start}&max={max}'


def main():
    ITEMS_START = 0
    ITEMS_FINISH = 2200
    ITEMS_BATCH = 100

    storage = DataStorage(collection_name='rtrt')

    index = ITEMS_START
    while index < ITEMS_FINISH:
        url = get_events_url(index, ITEMS_BATCH)
        logger.info(f'process url: {url}')

        updated_ids = storage.update(
            id_fields=['name'],
            list_url=url,
            list_update_frequency_sec=UPDATE_FREQUENCY_SEC,
            list_filter=ironman_filter,
            list_transformer=list_transformer,
            dry_run=False,
            limit=-1)
        logger.info(f'{len(updated_ids)} items updated')

        index += ITEMS_BATCH


if __name__ == '__main__':
    main()

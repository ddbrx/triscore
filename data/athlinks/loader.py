#!/usr/bin/env python3
from base import log, utils
from data.storage import DataStorage
import parser
import url

logger = log.setup_logger(__file__)

UPDATE_FREQUENCY_SEC = 86400
# UPDATE_FREQUENCY_SEC = 60


def list_events_transformer(data):
    return data['result']['events']


def main():
    ITEMS_START = 0
    # ITEMS_FINISH = 191940
    ITEMS_FINISH = 100
    ITEMS_BATCH = 10

    storage = DataStorage(
        collection_name='athlinks',
        indices=['masterEventTitle', [('masterEventTitle', 'text')]])

    index = ITEMS_START

    while index < ITEMS_FINISH:
        batch_url = url.get_races_url(
            startDate='2020-03-27', endDate='2020-03-27', skip=index, limit=ITEMS_BATCH,
            triathlon=True, sprint=True, olympic=True, halfIronman=True, ironmanAndUp=True)
        logger.info(
            f'from: {index} to: {index + ITEMS_BATCH} url: {batch_url}')

        break
        # updated_ids = storage.update(
        #     id_fields=['masterEventId'],
        #     list_url=batch_url,
        #     list_update_frequency_sec=UPDATE_FREQUENCY_SEC,
        #     list_transformer=list_events_transformer,
        #     dry_run=False)

        # if len(updated_ids) == 0:
        #     logger.info('no items updated: stop iterations')
        #     break

        # logger.info(f'{len(updated_ids)} items updated')
        # index += ITEMS_BATCH


if __name__ == '__main__':
    main()

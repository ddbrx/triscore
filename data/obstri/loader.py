#!/usr/bin/env python3
from base import log, utils
from data.storage import DataStorage
import parser
import url

logger = log.setup_logger(__file__)

UPDATE_FREQUENCY_SEC = 86400
# UPDATE_FREQUENCY_SEC = 60


def races_info_transformer(races_list):
    return races_list['racesInfo']


def races_v2_transformer(races_list):
    return races_list['racesv2']


def get_data_url(race):
    race_name = parser.get_race_name(race)
    race_year = parser.get_race_year(race)
    return url.get_results_url(race_name, race_year)


def load_races_v2():
    storage = DataStorage(collection_name='obstri', indices=['r'])

    updated_ids = storage.update(
        id_fields=['r', 'd'],
        list_url=url.RACES_URL,
        list_update_frequency_sec=UPDATE_FREQUENCY_SEC,
        list_transformer=races_v2_transformer,
        add_invalid=True,
        dry_run=False,
        limit=-1)
    logger.info(f'{len(updated_ids)} items updated')


def load_races_info():
    storage = DataStorage(collection_name='obstri_info')
    updated_ids = storage.update(
        id_fields=['r', 'd'],
        list_url=url.RACES_URL,
        list_update_frequency_sec=UPDATE_FREQUENCY_SEC,
        list_transformer=races_info_transformer,
        dry_run=False,
        limit=-1)
    logger.info(f'{len(updated_ids)} items updated')


def load_races_results():
    storage = DataStorage(collection_name='obstri_results')
    updated_ids = storage.update(
        id_fields=['r', 'd'],
        list_url=url.RACES_URL,
        list_update_frequency_sec=UPDATE_FREQUENCY_SEC,
        list_transformer=races_v2_transformer,
        data_url_field='results',
        data_url_transformer=get_data_url,
        dry_run=False,
        limit=-1)
    logger.info(f'{len(updated_ids)} items updated')


def main():
    # load_races_v2()
    # load_races_info()
    load_races_results()


if __name__ == '__main__':
    main()

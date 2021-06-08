#!/usr/bin/env python3
from base import log, dt
from data.storage import DataStorage
import parser
import url

logger = log.setup_logger(__file__)


def data_transformer(item):
    return item['data']


def is_ironman_full_or_half(race):
    brand = parser.get_event_brand(race)
    return brand == "IRONMAN" or brand == "IRONMAN 70.3"


def is_race(race):
    subevent_type = parser.get_subevent_type(race)
    return subevent_type == 'Race'


def is_date_in_the_past(race):
    date = parser.get_event_date(race)
    current_date = dt.date_to_string(dt.now(), dt.DATE_FORMAT)
    return date < current_date


def ironman_race_date_filter(race):
    valid_race = is_race(race) and is_ironman_full_or_half(race) and is_date_in_the_past(race)
    return not valid_race


def load_races(races_storage):
    LIMIT = 100
    FIRST_INDEX = 0
    LAST_INDEX = 50000
    for start_index in range(FIRST_INDEX, LAST_INDEX, LIMIT):
        races_batch_url = url.get_races_url(limit=LIMIT, skip=start_index)
        updated_ids = races_storage.update(
            id_fields=['SubEventId', 'Date'],
            list_url=races_batch_url,
            list_headers=url.API_HEADERS,
            list_update_frequency_sec=86400,
            list_transformer=data_transformer,
            list_filter=ironman_race_date_filter,
            dry_run=False,
            add_invalid=True,
            data_load_timeout=1,
            limit=-1)
        if updated_ids is None:
            logger.info(f'no races found url: {races_batch_url}: break')
            break
        else:
            logger.info(f'url: {races_batch_url} updated: {len(updated_ids)}')


def load_results(races_storage, db_name):
    for race in races_storage.find(
            where={DataStorage.INVALID_FIELD: False,
                   DataStorage.PROCESSED_FIELD: False},
            sort=[('Date', 1)]):
        race_name = parser.get_subevent_name(race)
        logger.info(f'process race {race_name}')

        subevent_id = parser.get_subevent_id(race)
        race_storage = DataStorage(
            db_name=db_name, collection_name=subevent_id)
        race_results_url = url.get_race_results_url(subevent_id=subevent_id)
        updated_ids = race_storage.update(
            id_fields=['ContactId'],
            list_url=race_results_url,
            list_headers=url.API_HEADERS,
            list_transformer=data_transformer,
            dry_run=False,
            data_load_timeout=1,
            limit=-1)

        if updated_ids is None:
            logger.info(
                f'no results found for race \'{race_name}\': mark as invalid')
            races_storage.mark_invalid(where={'SubEventId': subevent_id})
        else:
            logger.info(
                f'race \'{race_name}\' results were processed: {len(updated_ids)} items added: mark as processed')
            races_storage.mark_processed(where={'SubEventId': subevent_id})


def main():
    races_storage = DataStorage(db_name='ironman', collection_name='races')

    load_races(races_storage)
    load_results(races_storage, db_name='ironman')


if __name__ == '__main__':
    main()

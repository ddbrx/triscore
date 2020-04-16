#!/usr/bin/env python3
import argparse
from pymongo import MongoClient

from base import dt, log, utils
from race.storage import RaceStorage
import race.parser as race_parser

logger = log.setup_logger(__file__, debug=True)

name_map = {}

PRO_GROUPS = ['MPRO', 'FPRO']


def get_min_max_years(age_group):
    if age_group in PRO_GROUPS:
        return 18, 50

    if age_group.find('-') == -1:
        return 18, 90

    assert age_group[0] == 'M' or age_group[0] == 'F', f'unknown gender: {age_group}'

    splitted = age_group[1:].split('-')
    assert len(splitted) == 2, f'failed to split: {age_group}'

    lower_bound = int(splitted[0])
    upper_bound = int(splitted[1])
    assert lower_bound < upper_bound, f'wrong order: {lower_bound} >= {upper_bound}'

    return lower_bound, upper_bound


def get_min_max_birth_dates(age_group, date):
    lower_bound, upper_bound = get_min_max_years(age_group)
    min_birth_date = dt.delta(date, years=-upper_bound - 1, days=1)
    max_birth_date = dt.delta(date, years=-lower_bound)
    return min_birth_date, max_birth_date


def process_race(race_name, race_date, race_country, race_results, name_map):
    for race_result in race_results:
        athlete_name = race_parser.get_athlete_name(race_result)

        athlete_id = race_parser.get_athlete_id(race_result)
        athlete_country = race_parser.get_country_fifa_code(race_result)

        if athlete_name not in name_map:
            name_map[athlete_name] = {}

        if athlete_id not in name_map[athlete_name]:
            name_map[athlete_name][athlete_id] = {
                'dmin': dt.datetime(1900, 1, 1), 'dmax': dt.delta(dt.now(), years=18), 'races': []}

        age_group = race_parser.get_age_group(race_result)
        min_birth_date, max_birth_date = get_min_max_birth_dates(
            age_group, dt.date_from_string(race_date))
        assert min_birth_date <= max_birth_date, f'min birth date more than max birth date athlete_id: {athlete_id}'

        name_map[athlete_name][athlete_id]['dmin'] = max(
            name_map[athlete_name][athlete_id]['dmin'], min_birth_date)
        name_map[athlete_name][athlete_id]['dmax'] = min(
            name_map[athlete_name][athlete_id]['dmax'], max_birth_date)

        # assert name_map[athlete_name][athlete_id]['dmin'] <= name_map[athlete_name][athlete_id]['dmax'], f'min date more than max date athlete_id: {athlete_id} {athlete_name} {race_name} {race_date}'

        name_map[athlete_name][athlete_id]['races'].append(
            {'rd': race_date, 'rn': race_name, 'rc': race_country, 'a': age_group, 'c': athlete_country})


def insert_to_mongo(name_map, db_name, collection_name):
    mongo_client = MongoClient()
    collection = mongo_client[db_name][collection_name]
    collection.create_index('n', unique=True)
    collection.create_index('len')
    collection.create_index('l.id')

    for athlete_name, id_map in name_map.items():
        nc_athletes = []
        for athlete_id, dinfo in id_map.items():
            races = dinfo['races']

            athlete_info = {
                'id': athlete_id,
                'dmin': dt.date_to_string(dinfo['dmin']),
                'dmax': dt.date_to_string(dinfo['dmax']),
                'races': races
            }
            nc_athletes.append(athlete_info)

        nc_info = {
            'n': athlete_name,
            'len': len(nc_athletes),
            'l': nc_athletes
        }

        collection.insert_one(nc_info)


def main():
    logger.info('starting matcher')

    parser = argparse.ArgumentParser()
    parser.add_argument('--skip', type=int, default=0)
    parser.add_argument('--limit', type=int, default=0)
    parser.add_argument('--db-name', type=str, default='triscore-test')
    parser.add_argument('--collection-name', type=str, default='matcher')

    args = parser.parse_args()

    race_storage = RaceStorage()
    races = race_storage.get_races(skip=args.skip, limit=args.limit)
    count = races.count()

    name_map = {}
    for i, race_info in enumerate(races):
        race_name = race_parser.get_race_name(race_info)
        race_date = race_parser.get_race_date(race_info)
        race_country = race_parser.get_race_fifa_code(race_info)

        race_results = race_storage.get_race_results(race_name, race_date)

        logger.info(f'{i + 1}/{count}: {race_date} {race_name} {race_country}')
        process_race(race_name, race_date, race_country,
                     race_results, name_map)

    # insert_to_mongo(name_map, db_name=args.db_name,
    #                 collection_name=args.collection_name)


if __name__ == '__main__':
    main()

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


def process_race(race_name, race_date, race_results, name_map):
    for race_result in race_results:
        age_group = race_parser.get_age_group(race_result)
        # if age_group.find('-') == -1:
        #     continue

        athlete_name = race_parser.get_athlete_name(race_result)
        # encoded_athlete_name = athlete_name.encode('utf-8')

        athlete_id = race_parser.get_athlete_id(race_result)
        athlete_country = race_parser.get_country_fifa_code(race_result)

        nc_key = f'{athlete_name}:{athlete_country}'

        if nc_key not in name_map:
            name_map[nc_key] = {}

        if athlete_id not in name_map[nc_key]:
            name_map[nc_key][athlete_id] = {
                'dmin': dt.datetime(1930, 1, 1), 'dmax': dt.delta(dt.now(), years=18), 'races': []}

        min_birth_date, max_birth_date = get_min_max_birth_dates(
            age_group, dt.date_from_string(race_date))

        name_map[nc_key][athlete_id]['dmin'] = max(
            name_map[nc_key][athlete_id]['dmin'], min_birth_date)
        name_map[nc_key][athlete_id]['dmax'] = min(
            name_map[nc_key][athlete_id]['dmax'], max_birth_date)
        name_map[nc_key][athlete_id]['races'].append(
            {'d': race_date, 'n': race_name, 'a': age_group})


def insert_to_mongo(name_map, db_name, collection_name):
    mongo_client = MongoClient()
    collection = mongo_client[db_name][collection_name]
    collection.create_index('n')
    collection.create_index('c')
    collection.create_index('l.a')
    collection.create_index('l.id')

    for nc_key, id_map in name_map.items():
        # if len(id_map) == 1:
        #     continue
        nc_athletes = []
        for athlete_id, dinfo in id_map.items():
            races = dinfo['races']
            age_group_count = {}
            for race in races:
                age_group = race['a']
                if age_group not in age_group_count:
                    age_group_count[age_group] = 0
                age_group_count[age_group] += 1
            age_group = sorted(age_group_count.items(), key=lambda item: -item[1])[0][1]

            athlete_info = {
                'id': athlete_id,
                'a': age_group,
                'dmin': dt.date_to_string(dinfo['dmin']),
                'dmax': dt.date_to_string(dinfo['dmax']),
                'races': races
            }
            nc_athletes.append(athlete_info)

        name, country = nc_key.split(':')
        nc_info = {
            'n': name,
            'c': country,
            'l': nc_athletes
        }

        collection.insert_one(nc_info)


def main():
    logger.info('starting matcher')

    parser = argparse.ArgumentParser()
    parser.add_argument('--skip', type=int, default=0)
    parser.add_argument('--limit', type=int, default=0)

    args = parser.parse_args()

    race_storage = RaceStorage()
    races = race_storage.get_races(skip=args.skip, limit=args.limit)
    count = races.count()

    name_map = {}
    for i, race_info in enumerate(races):
        race_name = race_parser.get_race_name(race_info)
        race_date = race_parser.get_race_date(race_info)
        race_results = race_storage.get_race_results(race_name, race_date)

        logger.info(f'{i + 1}/{count}: {race_date} {race_name}')
        process_race(race_name, race_date, race_results, name_map)

    insert_to_mongo(name_map, db_name='triscore-test', collection_name='matcher')


if __name__ == '__main__':
    main()

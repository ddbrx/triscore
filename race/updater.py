#!/usr/bin/env python3
import argparse
from pymongo import MongoClient
from collections import Counter

from base import dt, log, utils
from race.storage import RaceStorage
import race.parser as race_parser

logger = log.setup_logger(__file__, debug=True)


def get_athlete_by_country(athletes):
    athlete_by_country = {}
    for athlete in athletes:
        athlete_id = athlete['id']
        races = athlete['races']
        country_counter = Counter(map(lambda race: race['c'], races))
        country = country_counter.most_common()[0][0]
        athlete_by_country.setdefault(country, []).append(athlete)
    return athlete_by_country


class Updater:
    def __init__(self, db_name, collection_name, prod):
        self.mongo_client = MongoClient()
        self.matcher_collection = self.mongo_client[db_name][collection_name]
        self.race_storage = RaceStorage()
        self.prod = prod

    def update(self, skip, limit, prod=False):
        matches = self.matcher_collection.find({'len': {'$gt': 1}}, sort=[
            ('len', -1)]).skip(skip).limit(limit)
        count = matches.count()
        id_replaced = 0
        for i, match in enumerate(matches):
            athlete_name = match['n']
            options_length = match['len']
            logger.debug(f'{i + 1}/{count}: {athlete_name} {options_length}')

            athletes = match['l']
            athlete_by_country = get_athlete_by_country(athletes)

            no_country_athletes = athlete_by_country.get('', [])
            no_country_athlete_used = len(no_country_athletes) == 0

            for country, athletes in athlete_by_country.items():
                if not country:
                    continue

                if len(athletes) == 1 and not no_country_athlete_used:
                    no_country_athlete_used = self.replace_athlete(
                        athlete_name, source_athlete=no_country_athletes[0], target_athlete=athletes[0])
                    id_replaced += no_country_athlete_used
                    continue

                if len(athletes) != 2:
                    continue

                def date_as_int(d):
                    return int(d.replace('-', ''))

                logger.debug(f'{country} {len(athletes)}')
                sorted_by_first_race = sorted(athletes, key=lambda a: a['races'][-1]['rd'])

                source_athlete = sorted_by_first_race[0]
                target_athlete = sorted_by_first_race[1]

                id_replaced += self.replace_athlete(
                    athlete_name, source_athlete, target_athlete)

        logger.info(f'id replaced: {id_replaced}')

    def replace_athlete(self, athlete_name, source_athlete, target_athlete):
        if not self.dates_of_birth_intersection(source_athlete, target_athlete):
            logger.debug(f'filter by date of birth\nsource: {source_athlete}\ntarget: {target_athlete}')
            return False

        if self.races_intersect(source_athlete['races'], target_athlete['races']):
            logger.debug(f'filter by race intersection\nsource: {source_athlete}\ntarget: {target_athlete}')
            return False

        source_id = source_athlete['id']
        source_races = source_athlete['races']
        target_id = target_athlete['id']
        logger.debug(
            f'DUPLICATE {athlete_name}: {len(source_races)} {source_id} -> {target_id}')

        for race in source_races:
            self.update_id(race=race, source_id=source_id, target_id=target_id)
        return True

    def races_intersect(self, races_a, races_b):
        def make_race_ids(races):
            races_ids = set()
            for race in races:
                race_name = race['rn']
                race_date = race['rd']
                races_ids.add(f'{race_name}:{race_date}')
            return races_ids
        race_ids_a = make_race_ids(races_a)
        race_ids_b = make_race_ids(races_b)
        return len(race_ids_a.intersection(race_ids_b)) > 0

    def dates_of_birth_intersection(self, athlete_a, athlete_b):
        def parse_dmin_max(athlete):
            return dt.date_from_string(athlete['dmin']), dt.date_from_string(athlete['dmax'])

        min_max_a = parse_dmin_max(athlete_a)
        min_max_b = parse_dmin_max(athlete_b)
        return not (min_max_a[0] > min_max_b[1] or min_max_a[1] < min_max_b[0])

    def update_id(self, race, source_id, target_id):
        race_name = race['rn']
        race_date = race['rd']
        if not self.prod:
            logger.info(
                f'DRY-RUN: {race_date} {race_name} {source_id} -> {target_id}')
        else:
            logger.debug(
                f'PROD {race_date} {race_name} {source_id} -> {target_id}')
            self.race_storage.update_athlete_id(
                race_date=race_date, race_name=race_name, source_athlete_id=source_id, target_athlete_id=target_id)


def main():
    logger.info('starting matcher')

    parser = argparse.ArgumentParser()
    parser.add_argument('--skip', type=int, default=0)
    parser.add_argument('--limit', type=int, default=0)
    parser.add_argument('--db-name', type=str, default='triscore-test')
    parser.add_argument('--collection-name', type=str, default='matcher')
    parser.add_argument('--prod', action='store_true')

    args = parser.parse_args()

    updater = Updater(args.db_name, args.collection_name, args.prod)
    updater.update(args.skip, args.limit)


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
import argparse
from pymongo import MongoClient
from collections import Counter

from base import dt, log, utils
from race.storage import RaceStorage
import race.parser as race_parser

logger = log.setup_logger(__file__, debug=True)


def get_athlete_by_country(athletes, filter_unknown=True):
    athlete_by_country = {}
    for athlete in athletes:
        athlete_id = athlete['id']

        races = athlete['races']
        if filter_unknown and any(map(lambda x: x['a'].find('-') == -1, races)):
            continue
        country_counter = Counter(map(lambda race: race['c'], races))
        country = country_counter.most_common()[0][0]
        athlete_by_country.setdefault(country, []).append(athlete)
    return athlete_by_country


def group_athletes_by_birth_date(athletes):
    def parse_dmin_max(athlete):
        return dt.date_from_string(athlete['dmin']), dt.date_from_string(athlete['dmax'])

    last_dmin, last_dmax = (None, None)
    groups = []
    last_group = {}
    for i, athlete in enumerate(sorted(athletes, key=lambda a: a['dmin'])):
        # logger.debug(athlete)
        athlete_id = athlete['id']
        athlete_races = athlete['races']
        athlete_races_len = len(athlete_races)
        dmin, dmax = parse_dmin_max(athlete)

        need_init = not last_dmax
        if last_dmax:
            if dmin <= last_dmax:
                last_dmin = dmin
                last_group[athlete_id] = athlete_races
            else:
                groups.append(last_group)
                need_init = True
        if need_init:
            last_dmin, last_dmax = dmin, dmax
            last_group = {athlete_id: athlete_races}

    groups.append(last_group)

    return groups


class Updater:
    def __init__(self, db_name, collection_name):
        self.mongo_client = MongoClient()
        self.matcher_collection = self.mongo_client[db_name][collection_name]
        self.race_storage = RaceStorage()

    def update(self, skip, limit, dry_run=True):
        matches = self.matcher_collection.find({'len': {'$gt': 1}}, sort=[
            ('len', 1)]).skip(skip).limit(limit)
        count = matches.count()
        for i, match in enumerate(matches):
            name = match['n']
            length = match['len']
            logger.debug(f'{i + 1}/{count}: {name} {length}')

            athletes = match['l']
            athlete_by_country = get_athlete_by_country(athletes)
            # logger.debug(athlete_by_country)

            no_country_athletes = athlete_by_country.get('', [])
            for country, athletes in athlete_by_country.items():
                if not country:
                    continue

                if len(athletes) == 1:
                    continue

                def date_as_int(d):
                    return int(d.replace('-', ''))

                # logger.debug(f'{country} {len(athletes)}')
                groups = group_athletes_by_birth_date(athletes)
                for group in groups:
                    sorted_group = sorted(
                        group.items(), key=lambda x: (-len(x[1]), -date_as_int(x[1][-1]['rd'])))
                    main_group = sorted_group[0]
                    main_id = main_group[0]
                    for duplicated_group in sorted_group[1:]:
                        duplicated_id = duplicated_group[0]
                        races = duplicated_group[1]
                        self.update_id(source_id=duplicated_id,
                                       target_id=main_id, races=races, dry_run=dry_run)

    def update_id(self, source_id, target_id, races, dry_run):
        for race in races:
            race_name = race['rn']
            race_date = race['rd']

            if dry_run:
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
    parser.add_argument('--dry-run', type=bool, default=True)

    args = parser.parse_args()

    updater = Updater(args.db_name, args.collection_name)
    updater.update(args.skip, args.limit)


if __name__ == '__main__':
    main()

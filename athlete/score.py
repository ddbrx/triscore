#!/usr/bin/env python3
import argparse
import os
from pymongo import MongoClient

from base import log, utils
import race.parser as race_parser
from race.storage import RaceStorage
from athlete.storage import AthleteStorage, MockAthleteStorage
from athlete.elo_scorer import EloScorer
import athlete.distribution as distribution


logger = log.setup_logger(__file__, debug=False)

START_SCORE = 1500
MIN_GROUP_SIZE = 10


def print_distribution(elo_scorer:EloScorer, log_file, index=None):
    top_athletes = elo_scorer.get_top_athletes()
    filename = os.path.basename(log_file) + (f'.{index}' if index else '')

    dir = os.path.join(os.path.dirname(log_file),
                        os.path.splitext(os.path.basename(log_file))[0])
    os.makedirs(dir, exist_ok=True)

    file = os.path.join(dir, filename)
    logger.info(f'flushing stats to {file}')
    with open(file, 'w') as f:
        if index:
            f.write(f'distribution #{index}\n')
        else:
            f.write('distribution total\n')

        for line in distribution.gen_chunks_distribution(top_athletes):
            f.write(line + '\n')

        f.write('\n----\n')

        for line in distribution.gen_distribution_by_score(top_athletes):
            f.write(line + '\n')

        f.write('top 100\n')
        top_100_athletes = list(top_athletes)[0:100]
        for i, line in enumerate(utils.gen_dicts(top_100_athletes, lj=30, filter_keys=['id', 'h', 'g'])):
            f.write(line + '\n')
            if i == 0:
                continue

            for hline in utils.gen_dicts(list(top_100_athletes[i - 1]['h']), lj=10):
                f.write(hline + '\n')

        f.write('last 100\n')
        last_100_athletes = list(top_athletes)[-100:]
        for i, line in enumerate(utils.gen_dicts(last_100_athletes, lj=30, filter_keys=['id', 'h', 'g'])):
            f.write(line + '\n')
            if i == 0:
                continue

            for hline in utils.gen_dicts(list(last_100_athletes[i - 1]['h']), lj=10):
                f.write(hline + '\n')

def main():
    logger.info('starting elo scorer')

    parser = argparse.ArgumentParser()

    parser.add_argument('-d', '--database', default='triscore')
    parser.add_argument('-u', '--username', default='triscore-writer')
    parser.add_argument('-p', '--password', required=True)

    parser.add_argument('--skip', type=int, default=0)
    parser.add_argument('--limit', type=int, default=0)
    parser.add_argument('--log-file', required=True)

    parser.add_argument('--A', type=int, default=6)
    parser.add_argument('--B', type=int, default=12)
    parser.add_argument('--C', type=int, default=3)

    parser.add_argument('--dry-run', action='store_true')

    args = parser.parse_args()

    mongo_client = MongoClient(username=args.username, password=args.password, authSource=args.database)
    if args.dry_run:
        athlete_storage = MockAthleteStorage()
    else:
        athlete_storage = \
                AthleteStorage(mongo_client=mongo_client, collection_name='athletes', create_indices=True)

    elo_scorer = EloScorer(athlete_storage, args.A, args.B, args.C)
    race_storage = RaceStorage(mongo_client=mongo_client, db_name='triscore')

    races = race_storage.get_races(skip=args.skip, limit=args.limit)
    race_count = races.count()

    for i, race_info in enumerate(races):
        race_date = race_parser.get_race_date(race_info)
        race_name = race_parser.get_race_name(race_info)
        logger.info(f'{args.skip + i + 1}/{race_count}: {race_date} {race_name}')

        race_results = race_storage.get_race_results(race_name=race_name, race_date=race_date)
        elo_scorer.add_race(race_info, race_results)

        if (args.skip + i + 1) % 100 == 0:
            print_distribution(elo_scorer, args.log_file, i + 1)

    print_distribution(elo_scorer, args.log_file,)


if __name__ == '__main__':
    main()

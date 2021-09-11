#!/usr/bin/env python3
import argparse
import os
from pymongo import MongoClient

from base import log, utils
import race.parser as race_parser
from race.storage import RaceStorage
from score.storage import AthleteStorage, MockAthleteStorage
from score.elo_scorer import EloScorer
# import score.distribution as distribution


logger = log.setup_logger(__file__, debug=False)

START_SCORE = 1500
MIN_GROUP_SIZE = 10


def print_distribution(elo_scorer:EloScorer, log_dir, index=None, extension='.txt'):
    os.makedirs(log_dir, exist_ok=True)
    filename = (f'{index}' if index else 'total') + extension
    filepath = os.path.join(log_dir, filename)

    # top_athletes = elo_scorer.get_top_athletes()

    logger.info(f'flushing stats to {filepath}')
    with open(filepath, 'w') as f:
        # if index:
        #     f.write(f'distribution #{index}\n')
        # else:
        #     f.write('distribution total\n')

        # for line in distribution.gen_chunks_distribution(top_athletes):
        #     f.write(line + '\n')

        # f.write('\n----\n')

        # for line in distribution.gen_distribution_by_score(top_athletes):
        #     f.write(line + '\n')

        f.write('top 100\n')
        FILTER_KEYS = ['id', 'h', 'g', 'c']
        DISPLAY_KEYS = ['date', 'type', 'a', 'as', 'ar', 'st', 'ns', 'da', 'eas', 'ear', 'etr', 'esr']
        top_100_athletes = list(elo_scorer.get_top_athletes(sort_order=-1, limit=100, with_history=True))
        logger.info(f'top_100_athletes: {top_100_athletes}')
        for i, line in enumerate(utils.gen_dicts(top_100_athletes, lj=30, filter_keys=FILTER_KEYS)):
            f.write(line + '\n')
            if i == 0:
                continue

            for hline in utils.gen_dicts(list(reversed(top_100_athletes[i - 1]['h'])), lj=10, display_keys=DISPLAY_KEYS, display_header=True):
                f.write('  ' + hline + '\n')

        f.write('last 100\n')
        last_100_athletes = list(elo_scorer.get_top_athletes(sort_order=1, limit=100, with_history=True))
        for i, line in enumerate(utils.gen_dicts(last_100_athletes, lj=30, filter_keys=FILTER_KEYS)):
            f.write(line + '\n')
            if i == 0:
                continue

            for hline in utils.gen_dicts(list(reversed(last_100_athletes[i - 1]['h'])), lj=10, display_keys=DISPLAY_KEYS, display_header=True):
                f.write('  ' + hline + '\n')

def main():
    logger.info('starting elo scorer')

    parser = argparse.ArgumentParser()

    parser.add_argument('-d', '--database', default='triscore')
    parser.add_argument('-u', '--username', default='triscore-writer')
    parser.add_argument('-p', '--password', required=True)

    parser.add_argument('--skip', type=int, default=0)
    parser.add_argument('--limit', type=int, default=0)
    parser.add_argument('--log-dir', default='/tmp/score')

    parser.add_argument('--dry-run', action='store_true')

    args = parser.parse_args()

    mongo_client = MongoClient(username=args.username, password=args.password, authSource=args.database, connect=False)

    if args.dry_run:
        athlete_storage = MockAthleteStorage()
    else:
        athlete_storage = \
                AthleteStorage(mongo_client=mongo_client, collection_name='athletes', create_indices=True)

    elo_scorer = EloScorer(athlete_storage)
    race_storage = RaceStorage(mongo_client=mongo_client, db_name='triscore')

    races = race_storage.get_races(skip=args.skip, limit=args.limit)
    race_count = races.count()

    for i, race_info in enumerate(races):
        race_date = race_parser.get_race_date(race_info)
        race_name = race_parser.get_race_name(race_info)
        logger.info(f'{args.skip + i + 1}/{race_count}: {race_date} {race_name}')

        race_results = race_storage.get_race_results(race_name=race_name, race_date=race_date)
        elo_scorer.add_race(race_info, race_results)

        if (args.skip + i) == 0 or (args.skip + i + 1) % 100 == 0:
            print_distribution(elo_scorer, args.log_dir, i + 1)

    print_distribution(elo_scorer, args.log_dir)


if __name__ == '__main__':
    main()

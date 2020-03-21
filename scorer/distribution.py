#!/usr/bin/env python3
import argparse

from base import log
from saver.tristats import mongo_api


logger = log.setup_logger(__file__)

TRISCORE_DB = 'triscore-test'

# api = mongo_api.ReadOnlyApi(dbname=TRISCORE_DB)
api = mongo_api.MongoApi(dbname=TRISCORE_DB)


def get_rating_and_race_count(country, limit):
    for athlete in api.get_top_athletes(country=country, limit=limit):
        yield int(athlete["rating"]), int(athlete["races"])


def print_distribution(country, limit):
    prev_index = -1
    races = []
    count = 0

    def dump_stats(index, count, races):
        median_races = sorted(races)[int(len(races) / 2)]
        print(
        f'[{index * 100}, {(index + 1)*100}) count: {count} races: {median_races}')

    for rating, race_count in get_rating_and_race_count(country, limit):
        index = int(rating / 100)
        if prev_index == -1:
            prev_index = index

        if index != prev_index:
            dump_stats(prev_index, count, races)
            races = []
            count = 0
            prev_index = index

        count += 1
        races.append(race_count)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=0)
    parser.add_argument('--country', type=str, default='')
    args = parser.parse_args()

    logger.info('args: {}'.format(args))

    print_distribution(args.country, args.limit)


if __name__ == '__main__':
    main()

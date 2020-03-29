#!/usr/bin/env python3
import argparse

from base import log
from score.storage import ScoreStorage


logger = log.setup_logger(__file__)


def get_score_and_race_count(athletes):
    for athlete in athletes:
        yield int(athlete['s']), int(athlete['p'])


def print_distribution(athletes):
    prev_index = -1
    races = []
    count = 0

    def dump_stats(index, count, races):
        median_races = sorted(races)[int(len(races) / 2)]
        print(
            f'[{index * 100}, {(index + 1)*100}) count: {count} races: {median_races}')

    for score, race_count in get_score_and_race_count(athletes):
        index = int(score / 100)
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

    score_storage = ScoreStorage()
    athletes = score_storage.get_top_athletes(
        country=args.country, limit=args.limit)
    print_distribution(athletes)


if __name__ == '__main__':
    main()
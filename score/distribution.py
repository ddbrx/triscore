#!/usr/bin/env python3
import argparse

from base import log
from score.storage import ScoreStorage


logger = log.setup_logger(__file__)


def get_score_and_race_count(athletes):
    for athlete in athletes:
        yield int(athlete['s']), int(athlete['p'])


def gen_distribution_by_score(athletes):
    prev_index = -1
    races = []
    count = 0

    for score, race_count in get_score_and_race_count(athletes):
        index = int(score / 100)
        if prev_index == -1:
            prev_index = index

        if index != prev_index:
            median_races = sorted(races)[int(len(races) / 2)]
            yield f'[{(index + 1) * 100}, {(index + 2)*100}) count: {count} races: {median_races}'
            races = []
            count = 0
            prev_index = index

        count += 1
        races.append(race_count)


def get_race_count_distribution(athletes):
    race_count_distribution = {}
    for athlete in athletes:
        p = athlete['p']
        if p not in race_count_distribution:
            race_count_distribution[p] = 0
        race_count_distribution[p] += 1
    return race_count_distribution


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=0)
    parser.add_argument('--country', type=str, default='')
    args = parser.parse_args()

    logger.info('args: {}'.format(args))

    score_storage = ScoreStorage()
    athletes = score_storage.get_top_athletes(
        country=args.country, limit=args.limit)
    # gen_distribution_by_score(athletes)
    race_count_distribution = get_race_count_distribution(athletes)
    print(f'races\t\tathletes=\t\tathletes>=\t\tpercent')
    total_athletes = sum(race_count_distribution.values())
    more_or_equal_athletes = total_athletes
    for p, count in sorted(race_count_distribution.items(), key=lambda x: -x[1]):
        percent = 100. * count / total_athletes
        print(f'{p}\t\t{count}\t\t{more_or_equal_athletes}\t\t{percent:.1f}')
        more_or_equal_athletes -= count


if __name__ == '__main__':
    main()

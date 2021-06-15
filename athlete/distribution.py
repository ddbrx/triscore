#!/usr/bin/env python3
import argparse
import bisect

from base import log
from athlete.storage import AthleteStorage


logger = log.setup_logger(__file__)


DEFAULT_CHUNKS = [1200, 1300, 1400, 1450, 1500, 1550, 1600, 1700,
                  1800, 1900, 2000, 2150, 2300, 2450, 2700, 3000, 3300]

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


def gen_chunks_distribution(athletes, chunks=DEFAULT_CHUNKS):
    prev_index = -1
    races = []
    count = 0

    def update(index):
        median_races = 0
        if len(races) > 0:
            median_races = sorted(races)[int(len(races) / 2)]

        lv = chunks[index]
        rv = chunks[index + 1] if (index + 1) < len(chunks) else '+inf'

        return f'[{lv}, {rv}) count: {count} races: {median_races}'

    for score, race_count in get_score_and_race_count(athletes):
        index = bisect.bisect_left(chunks, score) - 1
        if prev_index == -1:
            prev_index = index

        if index != prev_index:
            yield update(prev_index)
            races.clear()
            count = 0
            prev_index = index

        count += 1
        races.append(race_count)

    yield update(prev_index)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=0)
    parser.add_argument('--country', type=str, default='')
    args = parser.parse_args()

    logger.info('args: {}'.format(args))

    score_storage = AthleteStorage()
    athletes = score_storage.get_top_athletes(
        country=args.country, limit=args.limit)
    # gen_distribution_by_score(athletes)

    # race_count_distribution = get_race_count_distribution(athletes)
    # print(f'races\t\tathletes=\t\tathletes>=\t\tpercent')
    # total_athletes = sum(race_count_distribution.values())
    # more_or_equal_athletes = total_athletes
    # for p, count in sorted(race_count_distribution.items(), key=lambda x: -x[1]):
    #     percent = 100. * count / total_athletes
    #     print(f'{p}\t\t{count}\t\t{more_or_equal_athletes}\t\t{percent:.1f}')
    #     more_or_equal_athletes -= count

    for item in gen_chunks_distribution(athletes):
        print(item)


if __name__ == '__main__':
    main()

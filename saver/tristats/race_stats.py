#!/usr/bin/env python3
import log
import os
from fs_api import FsApi
import parser
import json
import utils

logger = log.setup_logger(__file__)


def main():
    api = FsApi()
    races = api.get_races_json(ascending=True)

    score_table = {}
    max_count = -1

    brand_to_races = {}
    for i, race in enumerate(races):
        if i == max_count:
            logger.info(f'stopping by max count: {max_count}')
            break

        race_url = race['RaceUrl']
        logger.info(f'{i + 1}/{len(races)}: {race_url}')

        brand = race_url.split('/')[1]
        if brand not in brand_to_races:
            brand_to_races[brand] = []

        brand_to_races[brand].append(race)

    summaries = []
    for i, (brand, races) in enumerate(brand_to_races.items()):
        total_races = len(races)
        total_participants = sum(race['RacerCount'] for race in races)
        summaries.append({'brand': brand,
                          'total_races': total_races,
                          'total_participants': total_participants})

    print('=== by total races')
    utils.print_dicts(sorted(summaries, key=lambda item: -item['total_races']))

    print('=== by total participants')
    utils.print_dicts(sorted(summaries, key=lambda item: -item['total_participants']))


if __name__ == '__main__':
    main()

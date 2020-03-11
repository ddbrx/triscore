#!/usr/bin/env python3
import log
import os
import parser
from mongo_api import MongoApi


logger = log.setup_logger(__file__)

TRISCORE_DB = 'triscore-test'


def main():
    logger.info('starting tricsore app')

    api = MongoApi(dbname=TRISCORE_DB)

    score_table = {}
    max_count = 1

    for i, race in enumerate(api.get_races(acsending=True)):
        if i == max_count:
            logger.info(f'stopping by max count: {max_count}')
            break

        race_name = race['RaceName']
        logger.info(f'{i + 1}: {race_name}')

        race_results = race['Results']
        for i, result in enumerate(race_results):
            name = parser.get_name(result['Racer'])
            profile = parser.get_profile(result, race)
            # print(f'{i}: {profile} {name}')


if __name__ == '__main__':
    main()

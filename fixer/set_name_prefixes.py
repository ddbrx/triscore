#!/usr/bin/env python3
import argparse
import json
import os

from base import log, utils, translit
from saver.tristats import mongo_api

logger = log.setup_logger(__file__)

TRISCORE_DB = 'triscore-test'

api = mongo_api.MongoApi(dbname=TRISCORE_DB)


def insert_prefixes(country, limit):
    cursor = api.get_top_athletes(country=country, limit=limit)
    count = cursor.count()
    for i, athlete in enumerate(cursor):
        athlete_name = athlete['name'].strip().lower()
        athlete_profile = athlete['profile']
        athlete_country = athlete['country']

        prefixes = _get_prefixes(athlete_name)
        if athlete_country == 'RUS':
            for translit_option in translit.get_translit_options(athlete_name):
                prefixes.extend(_get_prefixes(translit_option))

        logger.debug(f'{i + 1}/{count}: {athlete_profile} {athlete_name}: {prefixes}')
        api.update_athlete_field(athlete_profile, 'prefixes', prefixes)


def _get_prefixes(name):
    prefixes = []
    words = name.split()

    # insert subsets of words
    for i in range(2, 1 + len(words)):
        prefixes.append(' '.join(words[0:i]))
        prefixes.append(' '.join(reversed(words[0:i])))

    # insert prefixes of each word
    for word in words:
        for prefix_len in range(3, 1 + len(word)):
            prefixes.append(word[0:prefix_len])

    return prefixes


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=0)
    parser.add_argument('--country', type=str, default='')
    args = parser.parse_args()

    logger.info('args: {}'.format(args))

    insert_prefixes(args.country, args.limit)


if __name__ == '__main__':
    main()

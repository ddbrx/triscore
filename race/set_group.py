#!/usr/bin/env python3
import json
import os

from base import log, utils
from saver.tristats import mongo_api

logger = log.setup_logger(__file__)

TRISCORE_DB = 'triscore-test'

api = mongo_api.MongoApi(dbname=TRISCORE_DB)


def set_group():
    cursor = api.get_athletes()
    count = cursor.count()
    for i, athlete in enumerate(cursor):
        athlete_profile = athlete['profile']
        last_group = athlete['history'][-1]['group'].upper()
        logger.info(f'{i + 1}/{count}: {athlete_profile} {last_group}')
        api.update_athlete_field(athlete['profile'], 'group', last_group)


def main():
    set_group()


if __name__ == '__main__':
    main()

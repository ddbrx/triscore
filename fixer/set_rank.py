#!/usr/bin/env python3
import json
import os

from base import log, utils
from saver.tristats import mongo_api

logger = log.setup_logger(__file__)

TRISCORE_DB = 'triscore-test'

api = mongo_api.MongoApi(dbname=TRISCORE_DB)


def set_rank():
    for i, athlete in enumerate(api.get_top_athletes()):
        rank = i + 1
        logger.info(f'{rank}: {athlete}')
        api.update_athlete_field(athlete['profile'], 'rank', i + 1)


def main():
    set_rank()


if __name__ == '__main__':
    main()

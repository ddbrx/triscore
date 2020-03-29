#!/usr/bin/env python3
import json
import os

from base import log, utils
from score.storage import ScoreStorage

logger = log.setup_logger(__file__)

TRISCORE_DB = 'triscore-test'

def main():
    score_storage = ScoreStorage()
    athletes = score_storage.get_top_athletes()
    count = athletes.count()
    for i, athlete in enumerate(athletes):
        rank = i + 1
        logger.info(f'{i + 1}/{count}: {rank}\t{athlete["name"]}')
        score_storage.update_athlete_field(athlete["id"], 'rank', i + 1)


if __name__ == '__main__':
    main()

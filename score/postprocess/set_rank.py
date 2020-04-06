#!/usr/bin/env python3
import json
import os

from base import log, utils
from score.storage import ScoreStorage

logger = log.setup_logger(__file__)

TRISCORE_DB = 'triscore'

def main():
    score_storage = ScoreStorage()
    athletes = score_storage.get_top_athletes()
    count = athletes.count()
    rank = 0
    previous_score = 0
    equal_rank_count = 1
    for i, athlete in enumerate(athletes):
        id = athlete["id"]
        name = athlete['n']
        score = athlete['s']
        if score == previous_score:
            equal_rank_count += 1
        else:
            rank += equal_rank_count
            equal_rank_count = 1

        logger.info(f'{i + 1}/{count}: {rank}\t{name}')
        score_storage.update_athlete_field(id, 'r', rank)
        previous_score = score

if __name__ == '__main__':
    main()

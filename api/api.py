#!/usr/bin/env python3
import argparse
import json
import time

from flask import Flask, request
from flask_restful import Api, Resource

from base import log
from race.storage import RaceStorage
from score.storage import ScoreStorage

logger = log.setup_logger(__file__)

app = Flask(__name__)

race_storage = RaceStorage()
score_storage = ScoreStorage()


def add_rank(iterable, start_rank):
    items = []
    for i, item in enumerate(iterable):
        item['rank'] = start_rank + i
        items.append(item)
    return items


@app.route('/athletes')
def athletes():
    logger.info(request.args)

    sort_field = request.args.get('sort')

    sort_order = 1 if request.args.get('order') == 'asc' else -1
    index_from = int(request.args.get('from'))
    index_to = int(request.args.get('to'))
    filter_name = request.args.get('name', default='')
    filter_country = request.args.get('country', default='')

    logger.info(
        f'sort: {sort_field} order: {sort_order} from: {index_from} '
        f'to: {index_to} name: {filter_name} country: {filter_country}')

    cursor = score_storage.get_top_athletes(
        country=filter_country,
        name=filter_name,
        sort_field='s' if sort_field=='score' else 'p',
        sort_order=sort_order,
        skip=index_from,
        limit=(index_to - index_from + 1))

    athletes = add_rank(cursor, start_rank=index_from + 1)
    total_count = cursor.count(with_limit_and_skip=False)
    data = {
        'athletes': athletes,
        'total_count': total_count
    }
    return data, 200


@app.route('/athlete-details')
def athlete_details():
    athlete_id = request.args.get('id')
    logger.info(f'athlete_id: {athlete_id}')
    athletes = list(score_storage.get_athletes(athlete_ids=[athlete_id]))
    assert len(athletes) <= 1, f'multiple athletes match id: {athlete_id}'
    return athletes[0] if len(athletes) == 1 else {}, 200


if __name__ == '__main__':
    app.run(debug=True)

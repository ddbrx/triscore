#!/usr/bin/env python3
import argparse
import json
import time

from flask import Flask, request

from base import log
from race.storage import RaceStorage
from score.storage import ScoreStorage

logger = log.setup_logger(__file__)


app = Flask(__name__)

race_storage = RaceStorage(collection_name='races')
score_storage = ScoreStorage(collection_name='scores')


def add_qrank(iterable, start_rank):
    items = []
    for i, item in enumerate(iterable):
        item['qr'] = start_rank + i
        items.append(item)
    return items


@app.route('/races')
def races():
    logger.info(request.args)

    sort = request.args.get('sort')
    order = request.args.get('order')
    index_from = int(request.args.get('from'))
    index_to = int(request.args.get('to'))
    filter_name = request.args.get('name', default='')
    filter_country = request.args.get('country', default='')

    sort_field = 'date'
    if sort == 'total':
        sort_field = 'stats.t'
    elif sort == 'finished':
        sort_field = 'stats.s'
    elif sort == 'percent':
        sort_field = 'stats.p'
    elif sort == 'country':
        sort_field = 'location.c'

    sort_order = 1 if order == 'asc' else -1

    logger.info(
        f'sort_field: {sort_field} sort_order: {sort_order} from: {index_from} '
        f'to: {index_to} name: {filter_name} country: {filter_country}')

    cursor = race_storage.get_races(
        country=filter_country,
        name=filter_name,
        sort_field=sort_field,
        sort_order=sort_order,
        skip=index_from,
        limit=(index_to - index_from + 1))

    races = add_qrank(cursor, start_rank=index_from + 1)
    total_count = cursor.count(with_limit_and_skip=False)
    data = {
        'races': races,
        'total_count': total_count
    }
    return data, 200


@app.route('/race-details')
def race_details():
    logger.info(request.args)

    name = request.args.get('name')
    date = request.args.get('date')
    skip = int(request.args.get('skip'))
    limit = int(request.args.get('limit'))
    sort = request.args.get('sort', default='rank')
    order = request.args.get('order', default='asc')

    sort_field = 'results.or'
    if sort == 'rank':
        sort_field = 'results.or'
    elif sort == 'time':
        sort_field = 'results.t'

    sort_order = 1 if order == 'asc' else -1

    logger.info(
        f'name: {name} date: {date} skip: {skip} limit: {limit} sort_field: {sort_field} sort_order: {sort_order}')

    race_results_list = list(race_storage.get_race_results(
        name=name,
        date=date,
        sort_field=sort_field,
        sort_order=sort_order,
        skip=skip,
        limit=limit
    ))

    if len(race_results_list) > 0:
        athlete_ids = list(map(lambda x: x['results']['id'], race_results_list))
        race_name = race_results_list[0]['name']
        race_date = race_results_list[0]['date']
        score_by_id = score_storage.get_score_by_id_and_race(athlete_ids=athlete_ids, race_name=race_name, race_date=race_date)
        for race_result in race_results_list:
            athlete_id = race_result['results']['id']
            race_result['results'].update({'s': score_by_id[athlete_id]})

    data = {
        'data': race_results_list
    }

    return data, 200


@app.route('/athletes')
def athletes():
    logger.info(request.args)

    sort = request.args.get('sort')

    order = request.args.get('order')
    index_from = int(request.args.get('from'))
    index_to = int(request.args.get('to'))
    filter_name = request.args.get('name', default='')
    filter_country = request.args.get('country', default='')

    sort_field = 's'
    if sort == 'score':
        sort_field = 's'
    elif sort == 'races':
        sort_field == 'p'

    sort_order = 1 if order == 'asc' else -1

    logger.info(
        f'sort_field: {sort_field} sort_order: {sort_order} from: {index_from} '
        f'to: {index_to} name: {filter_name} country: {filter_country}')

    cursor = score_storage.get_top_athletes(
        country=filter_country,
        name=filter_name,
        sort_field=sort_field,
        sort_order=sort_order,
        skip=index_from,
        limit=(index_to - index_from + 1))

    athletes = add_qrank(cursor, start_rank=index_from + 1)
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
    app.run(host='0.0.0.0')

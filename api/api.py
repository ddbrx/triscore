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

MAX_ITEMS_LIMIT = 100

# race_storage = RaceStorage()
score_storage = ScoreStorage(collection_name='scores')


def add_rel_index(iterable, start_index):
    items = []
    for i, item in enumerate(iterable):
        item['i'] = start_index + i
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

    limit = min(MAX_ITEMS_LIMIT, index_to - index_from + 1)

    logger.info(
        f'sort_field: {sort_field} sort_order: {sort_order} from: {index_from} '
        f'to: {index_to} name: {filter_name} country: {filter_country}')

    race_storage = RaceStorage()
    races = race_storage.get_races(
        country=filter_country,
        name=filter_name,
        sort_field=sort_field,
        sort_order=sort_order,
        skip=index_from,
        limit=limit)

    total_count = races.count(with_limit_and_skip=False)
    data = {
        'data': list(races),
        'total': total_count
    }
    return data, 200


@app.route('/race-info')
def race_info():
    race_storage = RaceStorage()

    logger.info(request.args)

    race_name = request.args.get('name')
    race_date = request.args.get('date')

    logger.info(f'race_name: {race_name} race_date: {race_date}')

    race_info = race_storage.get_race_info(
        race_name=race_name,
        race_date=race_date,
    )

    data = {
        'data': race_info,
        'total': 1
    }
    return data, 200


@app.route('/race-results')
def race_results():
    race_storage = RaceStorage()

    logger.info(request.args)

    race_name = request.args.get('name')
    race_date = request.args.get('date')
    athlete_filter = request.args.get('athlete')
    country_filter = request.args.get('country')
    skip = int(request.args.get('skip'))
    limit = min(int(request.args.get('limit')), MAX_ITEMS_LIMIT)
    sort = request.args.get('sort', default='rank')
    order = request.args.get('order', default='asc')

    sort_field = 'or'
    if sort == 'rank':
        sort_field = 'or'

    sort_order = 1 if order == 'asc' else -1

    logger.info(
        f'race_name: {race_name} race_date: {race_date} athlete_filter: {athlete_filter} country_filter: {country_filter} skip: {skip} limit: {limit} sort_field: {sort_field} sort_order: {sort_order}')

    race_results = race_storage.get_race_results(
        race_name=race_name,
        race_date=race_date,
        athlete_filter=athlete_filter,
        country_filter=country_filter,
        sort_field=sort_field,
        sort_order=sort_order,
        skip=skip,
        limit=limit
    )

    total_count = race_results.count(with_limit_and_skip=False)
    race_results_list = list(race_results)

    if len(race_results_list) > 0:
        athlete_ids = list(map(lambda x: x['id'], race_results_list))
        scores_and_country_by_id = score_storage.get_scores_and_country(
            athlete_ids=athlete_ids, race_name=race_name, race_date=race_date)
        for i, race_result in enumerate(race_results_list):
            athlete_id = race_result['id']
            race_result.update(scores_and_country_by_id[athlete_id])
            race_result.update({'i': 1 + skip + i})

    data = {
        'data': race_results_list,
        'total': total_count
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
    limit = min(MAX_ITEMS_LIMIT, index_to - index_from + 1)

    logger.info(
        f'sort_field: {sort_field} sort_order: {sort_order} from: {index_from} '
        f'to: {index_to} name: {filter_name} country: {filter_country}')

    cursor = score_storage.get_top_athletes(
        country=filter_country,
        name=filter_name,
        sort_field=sort_field,
        sort_order=sort_order,
        skip=index_from,
        limit=limit)

    athletes = add_rel_index(cursor, start_index=index_from + 1)
    total_count = cursor.count(with_limit_and_skip=False)
    data = {
        'data': athletes,
        'total': total_count
    }
    return data, 200


@app.route('/athlete-details')
def athlete_details():
    athlete_id = request.args.get('id')
    logger.info(f'athlete_id: {athlete_id}')
    athlete = score_storage.get_athlete(athlete_id=athlete_id)
    data = {
        'data': athlete,
        'total': 1
    }
    return data, 200


if __name__ == '__main__':
    app.run(host='0.0.0.0')

#!/usr/bin/env python3
import argparse
import json
import time
from flask import Flask, request
from flask_restful import Api, Resource

from base import log
from saver.tristats import mongo_api

logger = log.setup_logger(__file__)

app = Flask(__name__)

TRISCORE_DB = 'triscore-test'

triscore_api = mongo_api.MongoApi(dbname=TRISCORE_DB)


def to_list_with_ids(iterable, start_id):
    items = []
    for i, item in enumerate(iterable):
        item['id'] = start_id + i
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

    cursor = triscore_api.get_top_athletes(
        country=filter_country,
        name=filter_name,
        sort_field=sort_field,
        sort_order=sort_order,
        skip=index_from,
        limit=(index_to - index_from + 1))

    athletes = to_list_with_ids(cursor, start_id=index_from + 1)
    total_count = cursor.count(with_limit_and_skip=False)
    data = {
        'athletes': athletes,
        'total_count': total_count
    }
    return data, 200


@app.route('/athlete-details')
def athlete_details():
    profile = request.args.get('profile', default='')
    logger.info(f'profile: {profile}')
    athlete = triscore_api.find_athlete(profile)
    return athlete if athlete else {}, 200


if __name__ == '__main__':
    app.run(debug=True)

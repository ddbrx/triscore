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
RECORDS_PER_PAGE = 100

triscore_api = mongo_api.MongoApi(dbname=TRISCORE_DB)


@app.route('/athletes')
def athletes():
    sort_field = request.args.get('sort')
    sort_order = 1 if request.args.get('order') == 'asc' else -1
    page = int(request.args.get('page'))
    name_filter = request.args.get('filter', default='')
    country_filter = request.args.get('country', default='')

    logger.info(
        f'sort: {sort_field} order: {sort_order} page: {page} filter: {name_filter} country_filter: {country_filter}')

    start_index = RECORDS_PER_PAGE * (page - 1)
    end_index = RECORDS_PER_PAGE * page
    logger.info(f'start_index: {start_index} end_index: {end_index}')

    cursor = triscore_api.get_top_athletes(
        country=country_filter,
        name_filter=name_filter, sort_field=sort_field, sort_order=sort_order, skip=start_index, limit=(end_index - start_index))
    total_count = cursor.count(with_limit_and_skip=False)
    data = {
        'athletes': list(cursor),
        'total_count': total_count
    }
    return data, 200


if __name__ == '__main__':
    app.run(debug=True)

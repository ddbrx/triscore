#!/usr/bin/env python3
import argparse
import json
import logging
import time
from flask import Flask, request
from flask_restful import Api, Resource

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

app = Flask(__name__)
# api = Api(app)

RATING_FILE = '/Users/dmitriyd/projects/triscore/score/test.json'
RECORDS_PER_PAGE = 7


@app.route('/athletes')
def athletes():
    sort = request.args.get('sort')
    order = request.args.get('order')
    page = int(request.args.get('page'))

    logger.info(f'sort: {sort} order: {order} page: {page}')

    index_from = RECORDS_PER_PAGE * (page - 1)
    index_to = RECORDS_PER_PAGE * page - 1
    logger.info(f'from: {index_from} to: {index_to}')

    with open(RATING_FILE) as f:
        j = json.load(f)
        users = []
        all_users = j['users']
        if order == 'asc':
            all_users.reverse()
        total_count = len(all_users)
        for i, user in enumerate(j['users']):
            if i < index_from:
                continue
            if i > index_to:
                break
            profile = user['profile']
            name = ' '.join(item.capitalize() for item in profile.split('/')[-1].split('-')[::-1])
            user['name'] = name
            users.append(user)

        data = {
            'users': users,
            'total_count': total_count
        }

        return data, 200


@app.route('/rating')
def rating():
    index_from = int(request.args.get('from'))
    index_to = int(request.args.get('to'))
    logger.info(f'from: {index_from} to: {index_to}')
    with open(RATING_FILE) as f:
        j = json.load(f)
        users = []
        all_users = j['users']
        count = len(all_users)
        for i, user in enumerate(j['users']):
            if i + 1 < index_from:
                continue
            if i + 1 > index_to:
                break
            profile = user['profile']
            name = ' '.join(item.capitalize() for item in profile.split('/')[-1].split('-')[::-1])
            user['name'] = name
            users.append(user)
        data = {
            'users': users,
            'total_count': count
        }
        return data, 200


if __name__ == '__main__':
    # api.add_resource(User, '/')
    app.run(debug=True)

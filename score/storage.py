import json
import re
from pymongo import MongoClient, ASCENDING, DESCENDING

from base import dt, log


logger = log.setup_logger(__file__, debug=True)

NO_LIMIT = 1000 * 1000 * 1000


class ScoreStorage:
    def __init__(self, collection_name='scores', dbname='triscore', create_indices=False):
        self.mongo_client = MongoClient()
        self.scores_collection = self.mongo_client[dbname][collection_name]
        if create_indices:
            self._create_indices()

    def get_top_athletes(self, name='', country='', age_group = '', sort_field='s', sort_order=DESCENDING, skip=0, limit=0):
        projection = {'_id': 0, 'h': 0, 'prefixes': 0}
        sort = [(sort_field, sort_order)]

        where = {}
        if country:
            where['c'] = country

        if age_group:
            where['a'] = age_group

        query = {}
        name = name.strip()
        if name:
            is_complex_filter = name.find(' ') != -1
            if is_complex_filter:
                # exact search
                name = f'\"{name}\"'

            text_query = {'$text': {'$search': name}}
            if len(where) > 0:
                query['$and'] = [
                    where,
                    text_query
                ]
            else:
                query = text_query
        else:
            query = where

        logger.info(f'query: \'{query}\' sort: {sort}')
        return self.scores_collection.find(
            query,
            sort=sort,
            projection=projection
        ).skip(skip).limit(limit)

    def get_athlete(self, athlete_id, projection={}):
        where = {'id': athlete_id}
        projection.update({'_id': 0})
        return self.scores_collection.find_one(where, projection=projection)

    def get_athletes(self, athlete_ids=[], projection={}):
        where = {}
        if len(athlete_ids) > 0:
            where = {'id': {'$in': athlete_ids}}
        projection.update({'_id': 0})
        return self.scores_collection.find(where, projection=projection)

    def get_score_by_id(self, athlete_ids=[]):
        score_by_id = {}
        for athlete in self.get_athletes(athlete_ids, projection={'id': 1, 's': 1}):
            athlete_id = athlete['id']
            score = athlete['s']
            score_by_id[athlete_id] = score
        return score_by_id

    def get_scores_and_country(self, race_name, race_date, athlete_ids=[]):
        score_by_id = {}
        for athlete in self.get_athletes(athlete_ids, projection={'id': 1, 'c': 1, 's': 1, 'h': 1}):
            athlete_id = athlete['id']

            found = False
            for race in athlete['h']:
                rn = race['race']
                rd = race['date']
                if rn == race_name and rd == race_date:
                    score = {'ps': race['ps'],
                             'ns': race['ns'], 'c': athlete['c']}
                    score_by_id[athlete_id] = score
                    found = True
                    break
            if not found:
                logger.warning(
                    f'score not found athlete_id: {athlete_id} race: {race_name} date: {race_date}')
                score_by_id[athlete_id] = {'ps': 0, 'ns': 0}

        return score_by_id

    def get_race_count_by_id(self, athlete_ids=[]):
        race_count_by_id = {}
        for athlete in self.get_athletes(athlete_ids, projection={'id': 1, 'p': 1}):
            athlete_id = athlete['id']
            race_count = athlete['p']
            race_count_by_id[athlete_id] = race_count
        return race_count_by_id

    def athlete_exists(self, athlete_id):
        return self.scores_collection.count_documents({'id': athlete_id}) > 0

    def add_athlete(self, athlete):
        return self.scores_collection.insert_one(athlete)

    def add_athlete_race(self, athlete_id, race_summary):
        country_code = race_summary['c']
        score = race_summary['ns']
        age_group = race_summary['a']
        race_count = race_summary['index']

        return self.scores_collection.update_one(
            {'id': athlete_id},
            {
                '$set': {'c': country_code, 's': score, 'p': race_count, 'a': age_group},
                '$push': {'h': race_summary}
            }
        )

    def update_athlete_field(self, athlete_id, field, value):
        return self.scores_collection.update_one(
            {'id': athlete_id},
            {
                '$set': {field: value}
            }
        )

    def update_athlete_array_field(self, athlete_id, field, single_value_or_list):
        value_clause = single_value_or_list
        if isinstance(single_value_or_list, list):
            value_clause = {'$each': single_value_or_list}
        return self.scores_collection.update_one(
            {'id': athlete_id},
            {
                '$push': {field: value_clause}
            }
        )

    def _create_indices(self):
        self.scores_collection.create_index('id', unique=True)
        self.scores_collection.create_index('n')
        self.scores_collection.create_index([('n', 'text')])
        self.scores_collection.create_index('g')
        self.scores_collection.create_index('c')
        self.scores_collection.create_index('a')
        self.scores_collection.create_index('p')
        self.scores_collection.create_index('s')
        # self.scores_collection.create_index(
        #     [('p', DESCENDING), ('s', DESCENDING)])
        # self.scores_collection.create_index(
        #     [('c', DESCENDING), ('s', DESCENDING)])


class MockScoreStorage:
    def __init__(self):
        self.athlete_by_id = {}

    def get_top_athletes(self, limit=0):
        list_limit = limit if limit != 0 else NO_LIMIT
        return sorted(
            list(self.athlete_by_id.values()), key=lambda item: -item['s'])[0:list_limit]

    def get_athletes(self, athlete_ids):
        athletes = []
        for athlete_id in athlete_ids:
            assert athlete_id in self.athlete_by_id, f'athlete not found id: {athlete_id}'
            athletes.append(self.athlete_by_id[athlete_id])
        return athletes

    def get_score_by_id(self, athlete_ids):
        return {
            athlete_id: self.athlete_by_id[athlete_id]['s'] for athlete_id in athlete_ids
        }

    def get_race_count_by_id(self, athlete_ids):
        return {
            athlete_id: self.athlete_by_id[athlete_id]['p'] for athlete_id in athlete_ids
        }

    def athlete_exists(self, athlete_id):
        return athlete_id in self.athlete_by_id

    def add_athlete(self, athlete):
        athlete_id = athlete['id']
        assert athlete_id not in self.athlete_by_id, f'duplicated athlete_id: {athlete_id}'
        self.athlete_by_id[athlete_id] = athlete

    def add_athlete_race(self, athlete_id, race_summary):
        assert athlete_id in self.athlete_by_id, f'athlete_id not found: {athlete_id}'

        self.athlete_by_id[athlete_id]['s'] = race_summary['ns']
        self.athlete_by_id[athlete_id]['p'] = race_summary['index']
        self.athlete_by_id[athlete_id]['a'] = race_summary['a']
        self.athlete_by_id[athlete_id]['c'] = race_summary['c']
        self.athlete_by_id[athlete_id]['h'].append(race_summary)

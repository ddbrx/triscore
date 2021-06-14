from bson import ObjectId
from pymongo import MongoClient
from base import log, translit

logger = log.setup_logger(__file__)


PROCESSED_FIELD = '_processed'


class TriscoreStorage:
    def __init__(self, mongo_client, db_name, create_indices=False):
        self.db = mongo_client[db_name]
        self.races_meta = self.db['meta']
        if create_indices:
            TriscoreStorage._create_meta_indices(self.races_meta)

    def get_races(self, name='', country='', race_type='', sort_field='date', sort_order=1, skip=0, limit=0, projection={}, batch_size=10):
        projection.update({'_id': 0})
        sort = [(sort_field, sort_order)]

        query = self._get_athlete_and_country_query(
            name, country, race_type=race_type, country_field='location.c')
        logger.info(f'query: \'{query}\'')
        return self.races_meta.find(
            query,
            sort=sort,
            projection=projection,
            batch_size=batch_size
        ).skip(skip).limit(limit)

    def count_races(self, name=None, date=None):
        f = {}
        if name:
            f['name'] = name
        if date:
            f['date'] = date
        return self.races_meta.count_documents(filter=f) > 0

    def get_race_info(self, race_name, race_date):
        race_meta = self._get_race_meta(name=race_name, date=race_date)
        if race_meta:
            del race_meta['_id']
            del race_meta['_processed']
            return race_meta
        return {}

    def get_race_results(self, race_name, race_date, athlete_filter='', country_filter='', age_group_filter='', sort_field='or', sort_order=1, skip=0, limit=0):
        race_id = self._get_race_id(race_name, race_date)
        if not race_id:
            log.error(
                f'no race id found race_name: {race_name} race_date: {race_date}')
            return []

        race_collection = self.db[race_id]
        query = self._get_athlete_and_country_query(
            athlete_filter, country_filter, age_group_filter=age_group_filter, country_field='c')
        projection = {'_id': 0}
        sort = [(sort_field, sort_order)]
        return race_collection.find(
            query,
            sort=sort,
            projection=projection
        ).skip(skip).limit(limit)

    def update_athlete_id(self, race_date, race_name, source_athlete_id, target_athlete_id):
        race_id = self._get_race_id(race_name, race_date)
        if not race_id:
            logger.warning(
                f'no race found to update athlete id: {race_name} {race_date}')
            return False

        race_collection = self.db[race_id]
        return race_collection.update_one({'id': source_athlete_id}, {'$set': {'id': target_athlete_id}})

    def add_race(self, info, results):
        race_name = info['name']
        race_date = info['date']

        assert not self.has_race(
            race_name, race_date), f'race already exists {race_name} {race_date}'

        try:
            info.update({PROCESSED_FIELD: False})
            inserted_id = self.races_meta.insert_one(info).inserted_id
            race_collection = self.db[str(inserted_id)]
            TriscoreStorage._create_data_indices(race_collection)
            inserted_ids = race_collection.insert_many(results).inserted_ids
        except Exception as exception:
            logger.error(f'failed to add race: {info} exception: {exception}')
            return False
        else:
            return len(inserted_ids) == len(results)

    def remove_race(self, name, date):
        race_id = self._get_race_id(name, date)
        if not race_id:
            logger.warning(f'no race found to remove: {name} {date}')
            return False

        logger.info(f'remove race meta {name} {date} {race_id}')
        self.races_meta.remove({'_id': ObjectId(race_id)})
        logger.info(f'drop race data {race_id}')
        self.db[race_id].drop()
        return True

    def get_race_length(self, name, date):
        race_id = self._get_race_id(name, date)
        if not race_id:
            return 0
        return self.db[race_id].count()

    def race_processed(self, name, date):
        race_meta = self._get_race_meta(name, date)
        return race_meta and race_meta[PROCESSED_FIELD]

    def set_race_processed(self, name, date, processed=True):
        race_id = self._get_race_id(name, date)
        if not race_id:
            logger.warning(
                f'cannot set processed: race does not exist: {name} {date}')
            return False
        return self.races_meta.update_one({'name': name, 'date': date}, {'$set': {PROCESSED_FIELD: processed}})

    def has_race(self, name, date):
        return self._get_race_id(name, date) != None

    def _get_athlete_and_country_query(self, name, country, race_type='', age_group_filter='', country_field='c'):
        conditions = []
        if country and country.strip():
            conditions.append({country_field: country.strip()})

        if age_group_filter and age_group_filter.strip():
            conditions.append({'a': age_group_filter.strip()})

        if race_type and race_type.strip():
            conditions.append({'type': race_type.strip()})

        if name and name.strip():
            options = [name.strip()]
            if name.find(' ') != -1:
                # exact search
                options = list(map(lambda x: '\"' + x + '\"', options))
            elif translit.has_cyrillic(name):
                options.extend(translit.cyrillic_to_english(name))

            search = ' '.join(options)
            conditions.append({'$text': {'$search': search}})

        query = {}
        if len(conditions) > 1:
            query = {
                '$and': conditions
            }
        elif len(conditions) == 1:
            query = conditions[0]
        return query

    def _get_race_id(self, name, date):
        race_meta = self._get_race_meta(name, date)
        return str(race_meta['_id']) if race_meta else None

    def _get_race_meta(self, name, date):
        return self.races_meta.find_one({'name': name, 'date': date})

    @staticmethod
    def _create_meta_indices(meta_collection):
        meta_collection.create_index(
            [('name', 1), ('date', -1)], unique=True)

        meta_collection.create_index([
            ('name', 'text'),
            ('location.continent', 'text'),
            ('location.country', 'text')
        ])

        meta_collection.create_index('date')
        meta_collection.create_index('brand')
        meta_collection.create_index('type')

        meta_collection.create_index('location.country_iso')
        meta_collection.create_index('location.continent')
        meta_collection.create_index('location.country')

        meta_collection.create_index('distance.td')
        meta_collection.create_index('distance.st')
        meta_collection.create_index('distance.bt')
        meta_collection.create_index('distance.rt')

        meta_collection.create_index('stats.m')
        meta_collection.create_index('stats.f')
        meta_collection.create_index('stats.t')
        meta_collection.create_index('stats.s')
        meta_collection.create_index('stats.p')

    @staticmethod
    def _create_data_indices(data_collection):
        data_collection.create_index('id', unique=True)
        data_collection.create_index([('n', 'text')])
        data_collection.create_index('n')
        data_collection.create_index('c')
        data_collection.create_index('b')
        data_collection.create_index('g')
        data_collection.create_index('a')
        data_collection.create_index('ar')
        data_collection.create_index('gr')
        data_collection.create_index('or')

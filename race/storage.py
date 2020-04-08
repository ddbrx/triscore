from pymongo import MongoClient
from base import log

logger = log.setup_logger(__file__)


PROCESSED_FIELD = '_processed'


class RaceStorage:
    def __init__(self, dbname):
        self.mongo_client = MongoClient()
        self.db = self.mongo_client[dbname]
        self.races_meta = self.db['meta']
        RaceStorage._create_meta_indices(self.races_meta)

    def get_races(self, name='', country='', sort_field='date', sort_order=1, skip=0, limit=0, exact_search=False):
        projection = {'_id': 0}
        sort = [(sort_field, sort_order)]

        conditions = []
        if country:
            conditions.append({'location.c': country})

        name = name.strip()
        if name:
            if exact_search:
                name = f'\"{name}\"'
            conditions.append({'$text': {'$search': name}})

        query = {}
        if len(conditions) > 1:
            query = {
                '$and': conditions
            }
        elif len(conditions) == 1:
            query = conditions[0]

        logger.info(f'query: \'{query}\'')
        return self.races_meta.find(
            query,
            sort=sort,
            projection=projection
        ).skip(skip).limit(limit)

    def count_races(self, name=None, date=None):
        f = {}
        if name:
            f['name'] = name
        if date:
            f['date'] = date
        return self.races_meta.count_documents(filter=f) > 0

    def get_race_results(self, name, date, sort_field, sort_order, skip=0, limit=0):
        race_meta = self._get_race_meta(name, date)
        if not race_meta:
            log.error(f'no race meta found name: {name} date: {date}')
            return []

        race_collection = self.db[str(race_meta['_id'])]
        query = {}
        projection = {'_id': 0}
        sort = [sort_field, sort_order]
        return race_collection.find(
            query,
            sort=sort,
            projection=projection
        )

    def add_race(self, info, results):
        race_name = info['name']
        race_date = info['date']

        assert not self.has_race(
            race_name, race_date), f'race already exists {race_name} {race_date}'

        try:
            info.update({PROCESSED_FIELD: False})
            inserted_id = self.races_meta.insert_one(info).inserted_id
            race_collection = self.db[str(inserted_id)]
            RaceStorage._create_data_indices(race_collection)
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
            return
        logger.info(f'dropping race {name} {date} {race_id}')
        self.db[race_id].drop_collection()

    def get_race_length(self, name, date):
        race_id = self._get_race_id(name, date)
        if not race_id:
            return 0
        return seld.db[race_id].count_documents()

    def race_processed(self, name, date):
        race_meta = self._get_race_meta(name, date)
        return race_meta and race_meta[PROCESSED_FIELD]

    def set_race_processed(self, name, date, processed):
        race_id = self._get_race_id(name, date)
        if not race_id:
            logger.warning(
                f'cannot set processed: race does not exist: {name} {date}')
            return False
        return self.races_meta.update_one({'name': name, 'date': date}, {'$set', {PROCESSED_FIELD: processed}})

    def has_race(self, name, date):
        return self._get_race_id(name, date) != None

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
            ('location.d', 'text'),
            ('location.cy', 'text'),
            ('location.c', 'text')])

        meta_collection.create_index('date')
        meta_collection.create_index('brand')
        meta_collection.create_index('type')

        meta_collection.create_index('location.d')
        meta_collection.create_index('location.ct')
        meta_collection.create_index('location.cy')
        meta_collection.create_index('location.c')

        meta_collection.create_index('distance.s.d')
        meta_collection.create_index('distance.s.t')
        meta_collection.create_index('distance.s.e')
        meta_collection.create_index('distance.b.d')
        meta_collection.create_index('distance.b.s')
        meta_collection.create_index('distance.b.e')
        meta_collection.create_index('distance.r.d')
        meta_collection.create_index('distance.r.s')
        meta_collection.create_index('distance.r.e')

        meta_collection.create_index('stats.t')
        meta_collection.create_index('stats.s')
        meta_collection.create_index('stats.p')
        meta_collection.create_index('stats.m')
        meta_collection.create_index('stats.f')

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

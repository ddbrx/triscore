#!/usr/bin/env python3
from base import log, utils
from data.storage import DataStorage
import parser

logger = log.setup_logger(__file__)


def main():
    storage = DataStorage(collection_name='ironman')

    races = storage.find(projection={"data": 0})
    count = races.count()

    max_count = -1
    brand_to_races = {}
    for i, race in enumerate(races):
        if i == max_count:
            logger.info(f'stopping by max count: {max_count}')
            break

        brand = parser.get_brand(race)

        if brand not in brand_to_races:
            brand_to_races[brand] = []

        brand_to_races[brand].append(race)

    summaries = []
    for i, (brand, races) in enumerate(brand_to_races.items()):
        total_races = len(races)
        summaries.append({'brand': brand,
                          'total_races': total_races})

    print('=== by total races')
    utils.print_dicts(sorted(summaries, key=lambda item: -item['total_races']))


if __name__ == '__main__':
    main()

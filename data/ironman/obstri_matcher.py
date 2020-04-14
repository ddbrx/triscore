import re
import unidecode

import parser
from base import log, utils
from data.storage import DataStorage

logger = log.setup_logger(__file__, debug=False)


class ObstriMatcher:
    def __init__(self):
        self.obstri_data = DataStorage(collection_name='obstri')
        self.obstri_info_data = DataStorage(collection_name='obstri_info')

    def find_race(self, full_name):
        name_no_year = parser.get_race_name_no_year(full_name)
        year = parser.get_race_year(full_name)
        tri_tag = parser.get_race_tri_tag(full_name)

        name_start_index = 2 if tri_tag else 1
        name_no_year_no_tag = ' '.join(name_no_year.split()[name_start_index:])

        obstri_r_race = self._find_race_by_r_y(
            name_no_year_no_tag, tri_tag, year)
        if obstri_r_race:
            return obstri_r_race

        obstri_rn_race = self._find_race_by_rn_y(
            name_no_year_no_tag, tri_tag, year)
        if obstri_rn_race:
            return obstri_rn_race

        return None

    def find_race_info(self, obstri_race):
        race_r = obstri_race['r']
        query = {'r': re.compile(race_r, re.IGNORECASE)}
        return self.obstri_info_data.find_one(query, sort=[('d', -1)])

    def _find_race_by_r_y(self, name_no_year_no_tag, tri_tag, year):
        to_remove = ['\'', '\t', '_', '-', '.', ':', 'course']

        pure_name = name_no_year_no_tag.lower()
        if pure_name.find('world') == -1:
            pure_name = pure_name.split('championship')[-1]

        if pure_name.find('(men)') != -1:
            tri_tag += 'm'
            to_remove.append('(men)')

        if pure_name.find('race 2') != -1:
            tri_tag += 'noswim'
            to_remove.append('race 2')

        for item in to_remove:
            pure_name = pure_name.replace(item, '')

        for sub_pure_name in utils.get_subsentences(pure_name):
            sub_short_name = sub_pure_name.replace(' ', '') + tri_tag
            query = {'r': sub_short_name}
            if sub_short_name.lower().find('vr') == -1:
                query.update({'y': year})

            races = list(self.obstri_data.find(query))
            logger.debug(f'query: {query} races: {len(races)}')
            if len(races) == 1:
                return races[0]

        return None

    def _find_race_by_rn_y(self, name_no_year_no_tag, tri_tag, year):
        brand_distance = parser.IRONMAN_BRAND
        if tri_tag:
            brand_distance += f' {tri_tag}'

        for rgx in [
            f'^{brand_distance} {name_no_year_no_tag}$',
            f'^{brand_distance} {name_no_year_no_tag}'
        ]:
            query = {'rn': re.compile(
                rgx, re.IGNORECASE), 'y': year, 'invalid': False}
            races = list(self.obstri_data.find(query))
            logger.debug(f'query: {query} races: {len(races)}')
            if len(races) == 1:
                return races[0]

        return None

API_URL = 'https://api.competitor.com'
API_HEADERS = {'wtc_priv_key': '90da38d91a0648f89823e375a43b2dc8'}


def get_race_results_url(subevent_id, limit=0, skip=0):
    return f'{API_URL}/public/result/subevent/{subevent_id}?%24limit={limit}&%24skip={skip}&%24sort%5BFinishRankOverall%5D=1'


def get_races_url(limit, skip=0):
    return f'{API_URL}/public/events?%24limit={limit}&%24skip={skip}'


def get_race_info_url(subevent_id):
    return f'{API_URL}/public/events/{subevent_id}'

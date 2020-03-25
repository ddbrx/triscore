RACES_URL='https://weh-api-public.azureedge.net/hasresults.json'

def get_results_url(event_id):
    return f'https://data.competitor.com/result/subevent/{event_id}?%24limit=0&%24skip=0&%24sort%5BFinishRankOverall%5D=1'

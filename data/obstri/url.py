RACES_URL='https://www.obstri.com/list.php'

def get_results_url(race_name, race_year):
    return f'{RACES_URL}?race={race_name}&year={race_year}&division=ALL'

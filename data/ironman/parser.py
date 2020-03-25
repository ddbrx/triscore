def get_event_name(race):
    return race['SubEvent']


def get_event_id(race):
    return race['SubEventId']


def get_brand(race):
    name = get_event_name(race)
    return name.split()[1]

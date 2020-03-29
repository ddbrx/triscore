ATHLKINS_RACE_API_URL = 'https://alaska.athlinks.com/events/race/api'


def get_races_url(startDate, endDate, skip=0, limit=10, sortBy='', searchTerm='', location='', withinRange='', running=False, upTo5k=False, from5kTo15k=False, from15kToHalfMara=False, fromHalfMaraToMara=False, marathon=False, ultra=False, triathlon=False, sprint=False, olympic=False, halfIronman=False, ironmanAndUp=False, aquathlon=False, aquabike=False, duathlon=False, more=False, swim=False, mountainBike=False, cycling=False, snow=False, adventure=False, obstacle=False, other=False):
    return \
        f'{ATHLKINS_RACE_API_URL}/find?running={running}&upTo5k={upTo5k}&from5kTo15k={from5kTo15k}&from15kToHalfMara={from15kToHalfMara}&fromHalfMaraToMara={fromHalfMaraToMara}&marathon={marathon}&ultra={ultra}&triathlon={triathlon}&sprint={sprint}&olympic={olympic}&halfIronman={halfIronman}&ironmanAndUp={ironmanAndUp}&aquathlon={aquathlon}&aquabike={aquabike}&duathlon={duathlon}&more={more}&swim={swim}&mountainBike={mountainBike}&cycling={cycling}&snow={snow}&adventure={adventure}&obstacle={obstacle}&other={other}&startDate={startDate}&endDate={endDate}&location={location}&withinRange={withinRange}&limit={limit}&skip={skip}&sortBy={sortBy}&searchTerm={searchTerm}'.lower()

def get_race_info(race_id):
    return f'{ATHLKINS_RACE_API_URL}/{race_id}'

# Data loading
## Races
https://api.competitor.com/public/events?%24limit=10&%24skip=0
{
    "total": 7697,
    "limit": 10,
    "skip": 0,
    "data": [
        {
            "SubEventId": "787C462B-7CAD-E911-A999-000D3A34EF1D",
            "Brand": "Non-series",
            "Series": "MK Marketo Test",
            "Event": "MK Marketo Test",
            "SubEvent": "MK Marketo Test",
            "SubEventType": "Race",
            "Date": "2019-11-18",
            "Latitude": 35.0456,
            "Longitude": -85.2672,
            "Alias": null,
            "StandardName": "MK Marketo Test",
            "BusinessUnit": "North America",
            "Timezone": null,
            "City": "Chattanooga",
            "StateOrProvince": "Tennessee",
            "CountryISONumeric": 840,
            "Sport": null,
            "DistanceInKM": null,
            "DistanceInMiles": null,
            "SyncDate": "2021-05-04T17:01:03.410Z",
            "Bike": null,
            "Swim": null,
            "Run": null,
            "AvgAirF": null,
            "AvgWaterF": null,
            "Airport": null,
            "EventImageURL": null,
            "Country": "United States",
            "PresentingPartner": null,
            "TitlePartner": null,
            "RaceWebpage": null,
            "ChampionshipDesignation": null,
            "Continent": "NA",
            "EventDay": 18,
            "EventMonth": 11,
            "EventYear": 2019,
            "RegistrationStatus": null
        },
        ...
    ]
}

## Race results
https://api.competitor.com/public/result/subevent/660190D0-BA16-E511-9402-005056951BF1?%24limit=10&%24skip=0&%24sort%5BFinishRankOverall%5D=1
{
    "total": 739,
    "limit": 10,
    "skip": 0,
    "data": [
        {
            "RunTimeConverted": "1:14:00",
            "SwimTimeConverted": "00:00:00",
            "BikeTimeConverted": "1:55:14",
            "FinishTimeConverted": "3:11:15",
            "Transition1TimeConverted": "00:01:05",
            "Transition2TimeConverted": "00:00:56",
            "CountryISO2": "BE",
            "SubeventName": "2015 IRONMAN 70.3 Bahrain",
            "ResultId": "A1360881-F0BF-4C30-8C34-533790C26FFC",
            "ContactId": "431F48D3-3FA6-4965-94DC-A899692314BE",
            "AgeGroup": "MPRO",
            "CountryRepresentingISONumeric": 56,
            "BibNumber": 34,
            "EventStatus": "Finish",
            "SwimTime": 0,
            "Transition1Time": 65,
            "BikeTime": 6914,
            "Transition2Time": 56,
            "RunTime": 4440,
            "FinishTime": 11475,
            "FinishRankGroup": 1,
            "FinishRankGender": 1,
            "FinishRankOverall": 1,
            "SwimRankGroup": 99999,
            "SwimRankGender": 99999,
            "SwimRankOverall": 99999,
            "BikeRankGroup": 1,
            "BikeRankGender": 1,
            "BikeRankOverall": 1,
            "RunRankGroup": 1,
            "RunRankGender": 1,
            "RunRankOverall": 1,
            "SyncDate": "2019-08-15T15:35:53.620Z",
            "SubEventId": "660190D0-BA16-E511-9402-005056951BF1",
            "RankPoints": 3500,
            "Contact": {
                "FullName": "Bart Aernouts",
                "Gender": "M"
            },
            "Country": {
                "ISO2": "BE"
            },
            "Subevent": {
                "SubEvent": "2015 IRONMAN 70.3 Bahrain"
            },
            "Badge_Result": null
        },
        ...
    ]
}

## Race info
https://api.competitor.com/public/events/660190D0-BA16-E511-9402-005056951BF1
{
    "SubEventId": "660190D0-BA16-E511-9402-005056951BF1",
    "Brand": "IRONMAN 70.3",
    "Series": "IRONMAN 70.3 Bahrain",
    "Event": "2015 IRONMAN 70.3 Bahrain",
    "SubEvent": "2015 IRONMAN 70.3 Bahrain",
    "SubEventType": "Race",
    "Date": "2015-12-05",
    "Latitude": null,
    "Longitude": null,
    "Alias": "bahrain70.3",
    "StandardName": "2015 IRONMAN 70.3 Bahrain",
    "BusinessUnit": "Middle East",
    "Timezone": "(GMT+03:00) Kuwait, Riyadh",
    "City": null,
    "StateOrProvince": null,
    "CountryISONumeric": null,
    "Sport": "Triathlon",
    "DistanceInKM": null,
    "DistanceInMiles": null,
    "SyncDate": "2021-05-03T05:00:17.610Z",
    "Bike": null,
    "Swim": null,
    "Run": null,
    "AvgAirF": null,
    "AvgWaterF": null,
    "Airport": null,
    "EventImageURL": null,
    "Country": null,
    "PresentingPartner": null,
    "TitlePartner": null,
    "RaceWebpage": null,
    "ChampionshipDesignation": null,
    "Continent": null,
    "EventDay": 5,
    "EventMonth": 12,
    "EventYear": 2015,
    "RegistrationStatus": null
}

# Mongo queries

## Distinct brands
ironman_races@mac.local> db.races.distinct("Brand")
[
	"5150 and International",
	"IRONKIDS",
	"IRONMAN",
	"IRONMAN 70.3",
	"IRONMAN Virtual Club",
	"Iron Girl",
	"Multisport Festivals",
	"Non-series",
	"Running",
	"Short Course Triathlon"
]


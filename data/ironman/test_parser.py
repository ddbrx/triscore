import pytest
import parser


def test_year_brand_race():
    assert parser.get_race_name_no_year(
        '2014 IRONMAN 70.3 European Championship') == 'IRONMAN 70.3 European Championship'


def test_year_month_brand_race():
    assert parser.get_race_name_no_year(
        '2012 June IRONMAN 70.3 Mandurah') == 'IRONMAN 70.3 Mandurah'

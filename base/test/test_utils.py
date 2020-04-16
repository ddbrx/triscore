from base import utils
import pytest


class TestGetSubsentences:
    def test_no_words(self):
        assert utils.get_subsentences('') == []

    def test_one_word(self):
        assert utils.get_subsentences('word') == ['word']

    def test_two_words(self):
        assert utils.get_subsentences('word1 word2') == [
            'word1 word2', 'word1', 'word2']


class TestGetKeyWithExtremeValue:
    def test_get_key_with_min_value(self):
        d = {'a': 5, 'b': 2, 'c': 3}
        assert utils.get_key_with_min_value(d) == 'b'

    def test_get_key_with_max_value(self):
        d = {'a': 5, 'b': 2, 'c': 3}
        assert utils.get_key_with_max_value(d) == 'a'

    def test_get_key_with_min_value_equal(self):
        d = {'a': 5, 'b': 5, 'c': 5}
        assert utils.get_key_with_min_value(d) == 'a'

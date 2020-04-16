from base import utils


class TestGetSubsentences:
    def test_no_words(self):
        assert utils.get_subsentences('') == []

    def test_one_word(self):
        assert utils.get_subsentences('word') == ['word']

    def test_two_words(self):
        assert utils.get_subsentences('word1 word2') == [
            'word1 word2', 'word1', 'word2']

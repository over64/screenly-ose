import unittest

from utils import url_fails
from utils import validate_url

url_fail = 'http://doesnotwork.example.com'
url_redir = 'http://example.com'
uri_ = '/home/user/file'


# url_timeout = 'http://...'


class UtilsTest(unittest.TestCase):
    def test_url_fails_1(self):
        self.assertTrue(url_fails(url_fail))

    def test_url_fails_2(self):
        self.assertFalse(url_fails(url_redir))

    def test_url_fails_3(self):
        self.assertFalse(url_fails(uri_))

    def test_valid_url(self):
        self.assertFalse(validate_url("hello"))
        self.assertFalse(validate_url("ftp://example.com"))
        self.assertFalse(validate_url("http://"))
        self.assertTrue(validate_url("http://wireload.net/logo.png"))
        self.assertTrue(validate_url("https://wireload.net/logo.png"))

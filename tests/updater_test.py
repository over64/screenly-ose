import updater
import unittest
from os import remove, path
from requests import RequestException
from sh import ErrorReturnCode


class attrdict(dict):
    def __getattr__(self, key):
        return self[key]


class UpdaterTest(unittest.TestCase):
    def test_is_up_to_date(self):
        update_fname = '/tmp/need_update'
        updater.UPDATE_FILE_NAME = update_fname

        with open(update_fname, 'w'):
            pass
        self.assertFalse(updater.is_up_to_date())

        remove(update_fname)
        self.assertTrue(updater.is_up_to_date())

    def test_get_last_sha(self):
        resp = attrdict(status_code=200, content=attrdict(strip=lambda: 'abcdef'))
        updater.req_get = lambda url: resp

        self.assertEqual(updater.get_last_sha(), 'abcdef')

        resp.status_code = 403
        self.assertEqual(updater.get_last_sha(), None)

        def raise_ex(url):
            raise RequestException

        updater.req_get = raise_ex
        self.assertEqual(updater.get_last_sha(), None)

    def test_local_version_has(self):
        def raise_ex(a, b, c):
            raise ErrorReturnCode(None, None, None)

        updater.git = raise_ex
        self.assertEquals(updater.local_version_has('abcdef'), False)

        updater.git = lambda a, b, c: 'feature'
        self.assertEquals(updater.local_version_has('abcdef'), False)

        updater.git = lambda a, b, c: 'feature\nmaster'
        self.assertEquals(updater.local_version_has('abcdef'), True)

    def test_set_need_update(self):
        update_fname = '/tmp/need_update'
        updater.UPDATE_FILE_NAME = update_fname

        updater.set_need_update(False)
        self.assertFalse(path.exists(update_fname))

        updater.set_need_update(True)
        self.assertTrue(path.exists(update_fname))

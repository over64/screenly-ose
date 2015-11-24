import unittest
from os import path
import os
from viewer import Scheduler
import viewer
from settings import settings
from datetime import datetime
import assets_helper
import db
import mock
from random import shuffle

TIME_WHERE_X_Y_ACTIVE = datetime(2015, 11, 26)
TIME_WHERE_Y_ACTIVE = datetime(2015, 11, 28)
TIME_WHERE_NO_ACTIVE = datetime(2015, 11, 29)
DB_FILE = '/tmp/test.db'

asset_x = {
    'mimetype': u'web',
    'asset_id': u'4c8dbce552edb5812d3a866cfe5f159d',
    'name': u'WireLoad',
    'uri': u'http://www.wireload.net',
    'start_date': datetime(2015, 11, 23),
    'end_date': datetime(2015, 11, 27),
    'duration': u'5',
    'is_enabled': 1,
    'nocache': 0,
    'play_order': 1,
}

asset_x_inactive = {
    'mimetype': u'web',
    'asset_id': u'4c8dbce552edb5812d3a866cfe5f159e',
    'name': u'WireLoad',
    'uri': u'http://www.wireload.net',
    'start_date': datetime(1970, 1, 1),
    'end_date': datetime(1970, 1, 1),
    'duration': u'5',
    'is_enabled': 1,
    'nocache': 0,
    'play_order': 1,
}

asset_y = {
    'mimetype': u'image',
    'asset_id': u'7e978f8c1204a6f70770a1eb54a76e9b',
    'name': u'Google',
    'uri': u'https://www.google.com/images/srpr/logo3w.png',
    'start_date': datetime(2015, 11, 25),
    'end_date': datetime(2015, 11, 29),
    'duration': u'6',
    'is_enabled': 1,
    'nocache': 0,
    'play_order': 0,
}

asset_y_inactive = {
    'mimetype': u'image',
    'asset_id': u'7e978f8c1204a6f70770a1eb54a76e9c',
    'name': u'Google',
    'uri': u'https://www.google.com/images/srpr/logo3w.png',
    'start_date': datetime(1970, 1, 1),
    'end_date': datetime(1970, 1, 1),
    'duration': u'6',
    'is_enabled': 1,
    'nocache': 0,
    'play_order': 0,
}


def tuned_shuffle(l):
    # shuffle([v1, v2], 0.1) -> [v2, v1]
    shuffle(l, lambda: 0.1)


class TestScheduler(unittest.TestCase):
    def setUp(self):
        viewer.HOME = '/tmp'

        self.set_now(TIME_WHERE_X_Y_ACTIVE)

        settings.set({
            'main': {'database': 'test.db'},
            'viewer': {'shuffle_playlist': False}
        })

        if os.path.exists(DB_FILE):
            os.remove(DB_FILE)

        self.conn = db.conn(DB_FILE)
        viewer.db_conn = self.conn

        with db.commit(self.conn) as cursor:
            cursor.execute(assets_helper.create_assets_table)
        self.scheduler = Scheduler()

    def tearDown(self):
        self.conn.close()

        viewer.shuffle = shuffle
        viewer.get_time = datetime.utcnow
        assets_helper.get_time = datetime.utcnow

    @classmethod
    def tearDownClass(cls):
        try:
            os.remove(DB_FILE)
        except: pass

    def set_now(self, t):
        viewer.get_time = lambda: t
        assets_helper.get_time = lambda: t

    def test_db_mtime(self):
        open(DB_FILE, 'w').close()
        mtime = path.getmtime(DB_FILE)

        self.assertEqual(mtime, Scheduler.get_db_mtime())

    def test_generate_asset_list_should_return_all_active(self):
        self.assertEqual(Scheduler.generate_asset_list(), ([], None))

        assets_helper.create_multiple(self.conn, [asset_x, asset_x_inactive, asset_y, asset_y_inactive])
        self.assertEqual(Scheduler.generate_asset_list(), ([asset_y, asset_x], asset_x['end_date']))

    def test_generate_asset_list_shuffled(self):
        settings['shuffle_playlist'] = True
        viewer.shuffle = tuned_shuffle

        assets_helper.create_multiple(self.conn, [asset_x, asset_y])

        pl = assets_helper.read(self.conn)
        tuned_shuffle(pl)

        pl_got, _ = Scheduler.generate_asset_list()
        self.assertEqual(pl, pl_got)

    def test_get_next_asset_on_empty_db_should_return_none(self):
        self.assertEqual(self.scheduler.get_next_asset(), None)

    def test_get_next_asset_should_update_pl_on_db_change(self):
        self.scheduler.refresh_playlist()

        assets_helper.create_multiple(self.conn, [asset_x])
        self.assertEqual(self.scheduler.get_next_asset(), asset_x)

    def test_get_next_asset_should_update_pl_on_deadline(self):
        assets_helper.create_multiple(self.conn, [asset_x, asset_y])
        self.scheduler.refresh_playlist()

        self.set_now(TIME_WHERE_Y_ACTIVE)

        self.assertEqual(asset_y, self.scheduler.get_next_asset())

    def test_get_next_asset_should_return_all_active_looped(self):
        assets_helper.create_multiple(self.conn, [asset_x, asset_x_inactive, asset_y, asset_y_inactive])

        self.assertEqual(asset_y, self.scheduler.get_next_asset())
        self.assertEqual(asset_x, self.scheduler.get_next_asset())
        self.assertEqual(asset_y, self.scheduler.get_next_asset())

    def test_get_next_asset_on_all_inactive_should_return_none(self):
        assets_helper.create_multiple(self.conn, [asset_x, asset_x_inactive, asset_y, asset_y_inactive])

        self.set_now(TIME_WHERE_NO_ACTIVE)

        self.assertEqual(None, self.scheduler.get_next_asset())

    def test_shuffle_should_invoke_after_MAX_REPEAT_reached(self):
        def dont_call_me():
            raise AssertionError('This call does not expected!')

        assets_helper.create_multiple(self.conn, [asset_x, asset_x_inactive, asset_y, asset_y_inactive])
        self.scheduler.refresh_playlist()

        viewer.SHUFFLE_MAX_REPEAT = 1
        settings['shuffle_playlist'] = True
        self.scheduler.update_playlist = dont_call_me

        self.scheduler.get_next_asset()
        self.scheduler.get_next_asset()

        update_pl_mock = mock.Mock(name='mocked update playlist')
        self.scheduler.update_playlist = update_pl_mock

        self.scheduler.get_next_asset()
        update_pl_mock.assert_called_once_with()

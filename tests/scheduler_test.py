import unittest
from os import path
import os
from viewer import Scheduler
import viewer
from settings import settings
from datetime import datetime
from datetime import timedelta
import assets_helper
import db
from random import Random
from random import shuffle

asset_x = {
    'mimetype': u'web',
    'asset_id': u'4c8dbce552edb5812d3a866cfe5f159d',
    'name': u'WireLoad',
    'uri': u'http://www.wireload.net',
    'start_date': datetime.utcnow() - timedelta(days=2),
    'end_date': datetime.utcnow() + timedelta(days=1),
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
    'start_date': datetime.utcnow() - timedelta(days=1),
    'end_date': datetime.utcnow() + timedelta(days=2),
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


class TestScheduler(unittest.TestCase):
    def setUp(self):
        viewer.HOME = '/tmp'
        self.db_file = '/tmp/test.db'

        if os.path.exists(self.db_file):
            os.remove(self.db_file)

        settings.set({
            'main': {'database': 'test.db'},
            'viewer': {'shuffle_playlist': False}
        })

        self.conn = db.conn(self.db_file)
        viewer.db_conn = self.conn

        with db.commit(self.conn) as cursor:
            cursor.execute(assets_helper.create_assets_table)
        self.scheduler = Scheduler()

    def tearDown(self):
        self.conn.close()

    def test_db_mtime(self):
        open(self.db_file, 'w').close()
        mtime = path.getmtime(self.db_file)

        self.assertEqual(mtime, Scheduler.get_db_mtime())

    def test_generate_asset_list_should_return_all_active(self):
        self.assertEqual(Scheduler.generate_asset_list(), ([], None))

        assets_helper.create_multiple(self.conn, [asset_x, asset_x_inactive, asset_y, asset_y_inactive])
        self.assertEqual(Scheduler.generate_asset_list(), ([asset_y, asset_x], asset_y['end_date']))

    def test_get_next_asset_on_empty_db_should_return_none(self):
        self.assertEqual(self.scheduler.get_next_asset(), None)

    def test_get_next_asset_should_update_pl_on_db_change(self):
        self.assertEqual(self.scheduler.get_next_asset(), None)

        assets_helper.create_multiple(self.conn, [asset_x])
        self.assertEqual(self.scheduler.get_next_asset(), asset_x)

    def test_get_next_asset_should_update_pl_on_deadline(self):
        assets_helper.create_multiple(self.conn, [asset_x, asset_y])
        self.scheduler.refresh_playlist()

        viewer.get_time = lambda: datetime.utcnow() + timedelta(days=10)
        assets_helper.get_time = lambda: datetime.utcnow() + timedelta(days=10)

        self.assertEqual(self.scheduler.get_next_asset(), None)

    # def test_update_pl(self):
    #     settings['shuffle_playlist'] = False
    #     assets_helper.create(self.conn, asset_x)
    #
    #     self.assertEquals(([asset_x], 0), Scheduler.update_pl([], 0))
    #     self.assertEquals(([asset_x], 0), Scheduler.update_pl([asset_x, asset_y], 1))
    #     self.assertEquals(([asset_x], 0), Scheduler.update_pl([asset_x], 0))
    #
    # def test_update_pl_shuffled(self):
    #     settings['shuffle_playlist'] = True
    #     rnd = Random().random()
    #
    #     assets_helper.create_multiple(self.conn, [asset_x, asset_y])
    #     assets, _ = Scheduler.update_pl(assets=[], index=0, shuffle_rnd=lambda: rnd)
    #
    #     shuffled = [asset_y, asset_x]
    #     shuffle(shuffled, lambda: rnd)
    #
    #     self.assertEquals(shuffled, assets)
    #
    # def test_take_next(self):
    #     # empty assets
    #     self.assertEqual(Scheduler.take([], 0), (None, 0))
    #
    #     # one active asset
    #     self.assertEqual(Scheduler.take([asset_x], 0), (asset_x, 0))
    #
    #     # one inactive asset
    #     self.assertEqual(Scheduler.take([asset_x_inactive], 0), (None, 0))
    #
    #     # two active
    #     self.assertEqual(Scheduler.take([asset_x, asset_y], 0), (asset_x, 1))
    #     self.assertEqual(Scheduler.take([asset_x, asset_y], 1), (asset_y, 0))
    #
    #     # inactive, active
    #     self.assertEqual(Scheduler.take([asset_x_inactive, asset_y], 0), (asset_y, 0))
    #     self.assertEqual(Scheduler.take([asset_x_inactive, asset_y], 1), (asset_y, 0))
    #
    #     # active, inactive
    #     self.assertEqual(Scheduler.take([asset_x, asset_y_inactive], 0), (asset_x, 1))
    #     self.assertEqual(Scheduler.take([asset_x, asset_y_inactive], 1), (asset_x, 1))
    #
    #     # 2 inactive
    #     self.assertEqual(Scheduler.take([asset_x_inactive, asset_y_inactive], 0), (None, 0))
    #     self.assertEqual(Scheduler.take([asset_x_inactive, asset_y_inactive], 1), (None, 0))
    #
    # def test_shuffle_correct_repeat_detection(self):
    #     self.assertEqual(Scheduler.shuffle_if_need([asset_x, asset_y], index=0, old_index=0, repeated=0), 1)
    #     self.assertEqual(Scheduler.shuffle_if_need([asset_x, asset_y], index=0, old_index=1, repeated=0), 1)
    #     self.assertEqual(Scheduler.shuffle_if_need([asset_x, asset_y], index=1, old_index=0, repeated=0), 0)
    #
    # def test_take_should_invoke_shuffle_after_MAX_REPEAT_reached(self):
    #     settings['shuffle_playlist'] = True
    #     viewer.SHUFFLE_MAX_REPEAT = 2
    #     pl_orig = [asset_x, asset_y]
    #     pl = [asset_x, asset_y]
    #     rnd = Random().random()
    #
    #     self.assertEqual(Scheduler.shuffle_if_need(pl, index=0, old_index=0, repeated=2, shuffle_rnd=lambda: rnd), 0)
    #     shuffle(pl_orig, lambda: rnd)
    #
    #     self.assertEqual(pl, pl_orig)

    # def my_shuffle(assets):
    #     rnd = Random.random()
    #
    #     def inner(a, b):
    #         shuffle(assets, rnd)
    #         shuffle(a, rnd)
    #
    #     return inner
    #
    # def test_get_next_asset_on_empty_assets_should_return_none(self):
    #     self.assertEqual(self.scheduler.get_next_asset(), None)
    #
    # def test_get_next_asset_on_one_inactive_should_return_none(self):
    #     assets_helper.create(self.conn, asset_x_inactive)
    #     self.assertEqual(self.scheduler.get_next_asset(), None)
    #
    # def test_get_next_asset_all_inactive_should_return_none(self):
    #     assets_helper.create_multiple(self.conn, [asset_x_inactive, asset_y_inactive])
    #     self.assertEqual(self.scheduler.get_next_asset(), None)
    #     self.assertEqual(self.scheduler.get_next_asset(), None)
    #
    # def test_get_next_asset_should_return_all_active(self):
    #     settings['shuffle_playlist'] = False
    #     assets_helper.create_multiple(self.conn, [asset_x, asset_x_inactive, asset_y, asset_y_inactive])
    #
    #     # first loop
    #     self.assertEqual(self.scheduler.get_next_asset(), asset_y)
    #     self.assertEqual(self.scheduler.get_next_asset(), asset_x)
    #
    #     # second loop
    #     self.assertEqual(self.scheduler.get_next_asset(), asset_y)
    #     self.assertEqual(self.scheduler.get_next_asset(), asset_x)
    #
    # def test_get_next_asset_should_shuffle_after_MAX_REPEAT(self):
    #     settings['shuffle_playlist'] = True
    #     viewer.SHUFFLE_MAX_REPEAT = 1
    #     pl = [asset_x, asset_x_inactive, asset_y, asset_y_inactive]
    #
    #     assets_helper.create_multiple(self.conn, pl)
    #     self.scheduler.update_pl()
    #
    #     def raise_error(a, b):
    #         raise Exception('Not now, bro')
    #
    #     viewer.shuffle = raise_error
    #
    #     # first loop
    #     self.assertEqual(self.scheduler.get_next_asset(), asset_y)
    #     self.assertEqual(self.scheduler.get_next_asset(), asset_x)
    #
    #     # second loop
    #     viewer.shuffle = self.my_shuffle(pl)
    #
    #     real_pl = filter(assets_helper.is_active, pl)
    #
    #     self.assertEqual(self.scheduler.get_next_asset(), real_pl[0])
    #     self.assertEqual(self.scheduler.get_next_asset(), real_pl[1])

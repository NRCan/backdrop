"""
Larger tests for the mongo storage engine.

This module includes integration tests and unit tests that require a significant
amount of setup and mocking. Small unit tests are in doctest format in the
module itself.
"""
from hamcrest import assert_that, is_, has_item, has_entries
from nose.tools import assert_raises
from mock import Mock

from pymongo.errors import CollectionInvalid, AutoReconnect

from backdrop.core.storage.mongo import MongoStorageEngine, reconnecting_save

from tests.support.test_helpers import d_tz


class TestMongoStorageEngine(object):
    def setup(self):
        self.engine = MongoStorageEngine.create(
            ['localhost'], 27017, 'backdrop_test')
        self.mongo = self.engine._mongo
        self.db = self.mongo['backdrop_test']

    def teardown(self):
        self.mongo.drop_database('backdrop_test')

    # ALIVE
    def test_alive_returns_true_if_mongo_is_up(self):
        assert_that(self.engine.alive(), is_(True))

    # EXISTS
    def test_exists_returns_false_if_data_set_does_not_exist(self):
        assert_that(self.engine.dataset_exists('foo_bar'), is_(False))

    def test_exists_returns_true_if_data_set_exists(self):
        self.db.create_collection('foo_bar')

        assert_that(self.engine.dataset_exists('foo_bar'), is_(True))

    # CREATE
    def test_create_a_non_capped_collection(self):
        self.engine.create_dataset('foo_bar', 0)

        assert_that(self.db.collection_names(), has_item('foo_bar'))
        assert_that(self.db['foo_bar'].options(), has_entries(
            {'capped': False}))

    def test_create_a_capped_collection(self):
        self.engine.create_dataset('foo_bar', 100)

        assert_that(self.db.collection_names(), has_item('foo_bar'))
        assert_that(self.db['foo_bar'].options(), has_entries(
            {'capped': True, 'size': 100}))

    def test_create_fails_if_collection_already_exists(self):
        # TODO: reraise a backdrop exception
        self.engine.create_dataset('foo_bar', 0)

        assert_raises(CollectionInvalid,
                      self.engine.create_dataset, 'foo_bar', 0)

    def _save(self, dataset_id, **kwargs):
        self.db[dataset_id].save(kwargs)

    # GET LAST UPDATED
    def test_get_last_udpated(self):
        self._save('foo_bar', _id='first', _updated_at=d_tz(2013, 3, 1))
        self._save('foo_bar', _id='second', _updated_at=d_tz(2013, 9, 1))
        self._save('foo_bar', _id='third', _updated_at=d_tz(2013, 3, 1))

        assert_that(self.engine.get_last_updated('foo_bar'),
                    is_(d_tz(2013, 9, 1)))

    def test_returns_none_if_there_is_no_last_updated(self):
        assert_that(self.engine.get_last_updated('foo_bar'), is_(None))

    # EMPTY
    def test_empty_a_dataset(self):
        self._save('foo_bar', _id='first')
        self._save('foo_bar', _id='second')

        assert_that(self.db['foo_bar'].count(), is_(2))

        self.engine.empty('foo_bar')

        assert_that(self.db['foo_bar'].count(), is_(0))

    # SAVE
    def test_save_a_record(self):
        self.engine.save('foo_bar', {'_id': 'first'})

        assert_that(self.db['foo_bar'].count(), is_(1))


class TestReconnectingSave(object):
    def test_reconnecting_save_retries(self):
        collection = Mock()
        collection.save.side_effect = [AutoReconnect, None]

        reconnecting_save(collection, 'record')

        assert_that(collection.save.call_count, is_(2))

    def test_reconnecting_save_fails_after_3_retries(self):
        collection = Mock()
        collection.save.side_effect = [AutoReconnect, AutoReconnect, AutoReconnect, None]

        assert_raises(AutoReconnect, reconnecting_save, collection, 'record')

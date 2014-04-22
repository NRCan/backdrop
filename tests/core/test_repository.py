import mock
import unittest

from backdrop.core.data_set import DataSetConfig
from backdrop.core.repository import (DataSetConfigRepository,
                                      UserConfigRepository,
                                      _get_json_url)
from hamcrest import assert_that, equal_to, is_, has_entries, match_equality
from mock import Mock, patch
from nose.tools import assert_raises
from backdrop.core.user import UserConfig
from contextlib import contextmanager
from os.path import dirname, join as pjoin
import requests


@contextmanager
def fixture(name):
    filename = pjoin(dirname(__file__), '..', 'fixtures', name)
    with open(filename, 'r') as f:
        yield f.read()

_GET_JSON_URL_FUNC = 'backdrop.core.repository._get_json_url'


class TestGetJsonUrl(unittest.TestCase):

    @patch('requests.get', spec=True)
    def test_get_json_url_sends_correct_request(self, mock_get):
        mock_response = Mock()
        mock_response.content = '[]'
        mock_get.return_value = mock_response
        response_content = _get_json_url("my_url", "some_token")
        mock_get.assert_called_once_with(
            'my_url',
            verify=False,
            headers={'content-type': 'application/json',
                     'Authorization': 'Bearer some_token'})
        assert_that(response_content, equal_to('[]'))


class TestDataSetRepository(unittest.TestCase):
    def setUp(self):
        self.data_set_repo = DataSetConfigRepository(
            'fake_stagecraft_url', 'fake_stagecraft_token')

    def test_retrieve_correctly_decodes_stagecraft_response(self):
        with fixture('stagecraft_get_single_data_set.json') as content:
            with mock.patch(_GET_JSON_URL_FUNC) as _get_json_url:
                _get_json_url.return_value = content

                data_set = self.data_set_repo.retrieve(name="data_set_name")

            expected_data_set = DataSetConfig("govuk_visitors",
                                           data_group="govuk",
                                           data_type="visitors",
                                           raw_queries_allowed=True,
                                           bearer_token="my-bearer-token",
                                           upload_format="excel",
                                           upload_filters="",
                                           auto_ids="",
                                           queryable=True,
                                           realtime=False,
                                           capped_size=None,
                                           max_age_expected=86400)

            assert_that(data_set, equal_to(expected_data_set))

    def test_get_all_correctly_decodes_stagecraft_response(self):
        with fixture('stagecraft_list_data_sets.json') as content:
            with mock.patch(_GET_JSON_URL_FUNC) as _get_json_url:
                _get_json_url.return_value = content

                data_sets = self.data_set_repo.get_all()

            expected_data_set_one = DataSetConfig(
                "govuk_visitors",
                data_group="govuk",
                data_type="visitors",
                raw_queries_allowed=True,
                bearer_token="my-bearer-token",
                upload_format="excel",
                upload_filters="",
                auto_ids="",
                queryable=True,
                realtime=False,
                capped_size=None,
                max_age_expected=86400)

            assert_that(len(data_sets), equal_to(5))
            assert_that(data_sets[0], equal_to(expected_data_set_one))

    def test_get_data_set_for_query_correctly_decodes_stagecraft_response(self):
        with fixture('stagecraft_query_data_group_type.json') as content:
            with mock.patch(_GET_JSON_URL_FUNC) as _get_json_url:
                _get_json_url.return_value = content

                data_set = self.data_set_repo.get_data_set_for_query(
                    data_group="govuk", data_type="realtime")

            expected_data_set = DataSetConfig("govuk_visitors",
                                           data_group="govuk",
                                           data_type="visitors",
                                           raw_queries_allowed=True,
                                           bearer_token="my-bearer-token",
                                           upload_format="excel",
                                           upload_filters="",
                                           auto_ids="",
                                           queryable=True,
                                           realtime=False,
                                           capped_size=None,
                                           max_age_expected=86400)

            assert_that(data_set, equal_to(expected_data_set))

    def test_retrieve_for_non_existent_data_set_returns_none(self):
        def _mock_raise_http_404(*args, **kwargs):
            mock_error_response = Mock()
            mock_error_response.status_code = 404
            exception = requests.HTTPError()
            exception.response = mock_error_response

            raise exception

        with mock.patch(_GET_JSON_URL_FUNC) as _get_json_url:
            _get_json_url.side_effect = _mock_raise_http_404
            data_set = self.data_set_repo.retrieve(name="non_existent")

        assert_that(data_set, is_(None))

    def test_retrieve_doesnt_catch_http_errors_other_than_404(self):
        def _mock_raise_http_503(*args, **kwargs):
            mock_error_response = Mock()
            mock_error_response.status_code = 503
            exception = requests.HTTPError()
            exception.response = mock_error_response

            raise exception

        with mock.patch(_GET_JSON_URL_FUNC) as _get_json_url:
            _get_json_url.side_effect = _mock_raise_http_503

            assert_raises(
                requests.HTTPError,
                lambda: self.data_set_repo.retrieve(name="non_existent"))

    def test_get_data_set_for_query_for_non_existent_data_set_returns_none(self):
        with mock.patch(_GET_JSON_URL_FUNC) as _get_json_url:
            _get_json_url.return_value = '[]'
            data_set = self.data_set_repo.get_data_set_for_query(
                data_group="govuk", data_type="realtime")

        assert_that(data_set, is_(None))

    def test_retrieve_calls_correct_url_for_data_set_by_name(self):
        with fixture('stagecraft_get_single_data_set.json') as content:
            with mock.patch(_GET_JSON_URL_FUNC) as _get_json_url:
                _get_json_url.return_value = content
                self.data_set_repo.retrieve(name="govuk_visitors")
                _get_json_url.assert_called_once_with(
                    'fake_stagecraft_url/data-sets/govuk_visitors',
                    "fake_stagecraft_token")

    def test_get_data_set_for_query_calls_correct_url(self):
        with fixture('stagecraft_query_data_group_type.json') as content:
            with mock.patch(_GET_JSON_URL_FUNC) as _get_json_url:
                _get_json_url.return_value = content
                self.data_set_repo.get_data_set_for_query(
                    data_group="govuk", data_type="realtime")
                _get_json_url.assert_called_once_with(
                    'fake_stagecraft_url/data-sets?'
                    'data-group=govuk&data-type=realtime',
                    "fake_stagecraft_token")

    def test_get_all_calls_correct_url(self):
        with fixture('stagecraft_query_data_group_type.json') as content:
            with mock.patch(_GET_JSON_URL_FUNC) as _get_json_url:
                _get_json_url.return_value = content
                self.data_set_repo.get_all()
                _get_json_url.assert_called_once_with(
                    'fake_stagecraft_url/data-sets', "fake_stagecraft_token")


class TestUserConfigRepository(object):
    def setUp(self):
        self.db = Mock()
        self.mongo_collection = Mock()
        self.db.get_collection.return_value = self.mongo_collection
        self.repository = UserConfigRepository(self.db)

    def test_saving_a_user_config(self):
        user = UserConfig("test@example.com",
                          data_sets=["data_set_one", "data_set_two"])

        self.repository.save(user)
        self.mongo_collection.save.assert_called_with(
            match_equality(has_entries({
                "_id": "test@example.com",
                "data_sets": ["data_set_one", "data_set_two"]
            }))
        )

    def test_saving_fails_with_non_user_config_object(self):
        not_user = {"foo": "bar"}

        assert_raises(ValueError, self.repository.save, not_user)

    def test_retrieving_a_user_config(self):
        self.mongo_collection.find_one.return_value = {
            "_id": "test@example.com",
            "email": "test@example.com",
            "data_sets": ["foo", "bar"],
        }

        user_config = self.repository.retrieve(email="test@example.com")
        expected_user_config = UserConfig("test@example.com", ["foo", "bar"])

        assert_that(user_config, equal_to(expected_user_config))

    def test_retrieving_non_existent_user_config_returns_none(self):
        self.mongo_collection.find_one.return_value = None
        user_config = self.repository.retrieve(email="test@example.com")

        assert_that(user_config, is_(None))

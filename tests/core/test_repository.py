import mock
import unittest

from backdrop.core.data_set import DataSetConfig
from backdrop.core.repository import (DataSetConfigRepository,
                                      UserConfigHttpRepository,
                                      get_user_repository,
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


def _mock_raise_http_404(*args, **kwargs):
    mock_error_response = Mock()
    mock_error_response.status_code = 404
    exception = requests.HTTPError()
    exception.response = mock_error_response

    raise exception


def _mock_raise_http_503(*args, **kwargs):
    mock_error_response = Mock()
    mock_error_response.status_code = 503
    exception = requests.HTTPError()
    exception.response = mock_error_response

    raise exception


def _raises_value_error_when_identifier_empty(repo):
    with assert_raises(ValueError) as e:
        repo.retrieve("")

    assert_that(str(e.exception), is_('the identifier must not be empty'))


_GET_JSON_URL_FUNC = 'backdrop.core.repository._get_json_url'


class TestGetUserRepository(unittest.TestCase):

    def build_app(self, config):
        app = Mock()
        app.config = config
        return app

    @patch('backdrop.core.repository.UserConfigHttpRepository', spec=True)
    def test_returns_correct_user_http_repository_when_turned_on(
            self,
            MockUserConfigHttpRepository):
        config = {
            'STAGECRAFT_URL': "some_url",
            'STAGECRAFT_DATA_SET_QUERY_TOKEN': "wibble",
        }
        get_user_repository(self.build_app(config))
        MockUserConfigHttpRepository.assert_called_once_with(
            'some_url',
            'wibble')


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
            'https://fake_stagecraft_url', 'fake_stagecraft_token')

    def test_retrieve_correctly_decodes_stagecraft_response(self):
        with fixture('stagecraft_get_single_data_set.json') as content:
            with mock.patch(_GET_JSON_URL_FUNC) as _get_json_url:
                _get_json_url.return_value = content

                data_set = self.data_set_repo.retrieve(
                    data_set_name="data_set_name")

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

    def test_get_data_set_for_query_correctly_decodes_stagecraft_response(
            self):
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
        with mock.patch(_GET_JSON_URL_FUNC) as _get_json_url:
            _get_json_url.side_effect = _mock_raise_http_404
            data_set = self.data_set_repo.retrieve(
                data_set_name="non_existent")

        assert_that(data_set, is_(None))

    def test_retrieve_doesnt_catch_http_errors_other_than_404(self):
        with mock.patch(_GET_JSON_URL_FUNC) as _get_json_url:
            _get_json_url.side_effect = _mock_raise_http_503

            assert_raises(
                requests.HTTPError,
                lambda: self.data_set_repo.retrieve(
                    data_set_name="non_existent"))

    def test_get_data_set_for_query_for_non_existent_data_set_returns_none(
            self):
        with mock.patch(_GET_JSON_URL_FUNC) as _get_json_url:
            _get_json_url.return_value = '[]'
            data_set = self.data_set_repo.get_data_set_for_query(
                data_group="govuk", data_type="realtime")

        assert_that(data_set, is_(None))

    def test_retrieve_calls_correct_url_for_data_set_by_name(self):
        with fixture('stagecraft_get_single_data_set.json') as content:
            with mock.patch(_GET_JSON_URL_FUNC) as _get_json_url:
                _get_json_url.return_value = content
                self.data_set_repo.retrieve(data_set_name="govuk_visitors")
                _get_json_url.assert_called_once_with(
                    'https://fake_stagecraft_url/data-sets/govuk_visitors',
                    "fake_stagecraft_token")

    def test_get_data_set_for_query_calls_correct_url(self):
        with fixture('stagecraft_query_data_group_type.json') as content:
            with mock.patch(_GET_JSON_URL_FUNC) as _get_json_url:
                _get_json_url.return_value = content
                self.data_set_repo.get_data_set_for_query(
                    data_group="govuk", data_type="realtime")
                _get_json_url.assert_called_once_with(
                    'https://fake_stagecraft_url/data-sets?'
                    'data-group=govuk&data-type=realtime',
                    "fake_stagecraft_token")

    def test_get_all_calls_correct_url(self):
        with fixture('stagecraft_query_data_group_type.json') as content:
            with mock.patch(_GET_JSON_URL_FUNC) as _get_json_url:
                _get_json_url.return_value = content
                self.data_set_repo.get_all()
                _get_json_url.assert_called_once_with(
                    'https://fake_stagecraft_url/data-sets',
                    "fake_stagecraft_token")

    def test_retrieve_throws_value_error_if_email_is_empty(self):
        _raises_value_error_when_identifier_empty(self.data_set_repo)


class TestUserConfigHttpRepository(object):
    def setUp(self):
        self.user_repo = UserConfigHttpRepository(
            'https://fake_stagecraft_url', 'fake_stagecraft_token')

    def test_saving_fails_with_not_implemented_error(self):
        user_config = {"foo": "bar"}

        assert_raises(NotImplementedError, self.user_repo.save, user_config)

    def test_retrieving_a_user_config(self):
        with fixture('stagecraft_user_config.json') as content:
            with mock.patch(_GET_JSON_URL_FUNC) as _get_json_url:
                _get_json_url.return_value = content

                user_config = self.user_repo.retrieve(email="test@example.com")

            expected_user_config = UserConfig(
                "test@example.com",
                ["foo", "bar"])

            assert_that(user_config, equal_to(expected_user_config))
            _get_json_url.assert_called_once_with(
                'https://fake_stagecraft_url/users/test%40example.com',
                'fake_stagecraft_token')

    def test_retrieve_for_non_existent_user_config_returns_none(self):
        with mock.patch(_GET_JSON_URL_FUNC) as _get_json_url:
            _get_json_url.side_effect = _mock_raise_http_404
            user = self.user_repo.retrieve(email="non_existent")

        assert_that(user, is_(None))

    def test_retrieve_doesnt_catch_http_errors_other_than_404(self):
        with mock.patch(_GET_JSON_URL_FUNC) as _get_json_url:
            _get_json_url.side_effect = _mock_raise_http_503

            assert_raises(
                requests.HTTPError,
                lambda: self.user_repo.retrieve(email="non_existent"))

    def test_retrieve_throws_value_error_if_email_is_empty(self):
        _raises_value_error_when_identifier_empty(self.user_repo)

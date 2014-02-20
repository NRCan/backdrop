import logging
import os
import sys
from backdrop.core.log_handler import get_log_file_handler
from features.support.splinter_client import SplinterClient

sys.path.append(
    os.path.join(os.path.dirname(__file__), '..')
)

os.environ["GOVUK_ENV"] = "test"

from support.flask_test_client import FlaskTestClient
from backdrop.read import api as read_api
from backdrop.write import api as write_api
# pick one for test configuration, if they don't match things will fail
from backdrop.write.config import test as config


handler = logging.FileHandler('log/behave.log')
handler.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)s - %(name)s - %(filename)s:%(lineno)d] "
    "-> %(message)s"))


log = logging.getLogger()
log.addHandler(handler)


def before_feature(context, feature):
    context.client = create_client(feature)


def before_scenario(context, _):
    context.client.before_scenario()
    storage = context.client.storage()
    storage.connection.drop_database(storage.name)
    context.after_handlers = []


def after_scenario(context, scenario):
    context.client.after_scenario(scenario)
    for handler in context.after_handlers:
        try:
            handler()
        except Exception as e:
            log.exception(e)


def after_feature(context, _):
    context.client.spin_down()


def create_client(feature):
    if 'use_admin_client' in feature.tags:
        if os.environ.get('SKIP_SPLINTER_TESTS'):
            class DummyClient(object):
                def spin_down(self):
                    pass
            return DummyClient()

        return SplinterClient(config.DATABASE_NAME, 'admin', '5002')
    else:
        return FlaskTestClient(read_api, write_api)

    raise AssertionError(
        "Test client not selected! Please annotate the failing feature with "
        + "either @use_read_api_client, @use_write_api_client "
        + "or @use_http_client.")

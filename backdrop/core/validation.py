"""Validators and validation related functions and types.

Validators should validate a specific type of thing and return a boolean.
App specific validation functions combine validators and return a
ValidationResult object.
"""
from collections import namedtuple
import jsonschema
import json
import datetime
import re
import bson
from dateutil import parser
import pytz


RESERVED_KEYWORDS = (
    '_timestamp',
    '_start_at',
    '_end_at',
    '_id',
)
VALID_KEY = re.compile('^[a-z_][a-z0-9_]+$')


def _is_real_date(value):
    try:
        parser.parse(value).astimezone(pytz.UTC)
        return True
    except (TypeError, ValueError):
        return False


def _is_valid_format(value):
    time_pattern = re.compile(
        "[0-9]{4}-[0-9]{2}-[0-9]{2}"
        "T[0-9]{2}:[0-9]{2}:[0-9]{2}"
        "(?:[+-][0-9]{2}:?[0-9]{2}|Z)"
    )
    return bool(time_pattern.match(value))


def value_is_valid_datetime_string(value):
    return _is_valid_format(value) and _is_real_date(value)


def value_is_valid(value):
    return isinstance(value, (int, float, basestring, bool, datetime.datetime,
                              bson.ObjectId)) or value is None


def key_is_valid(key):
    if not isinstance(key, basestring):
        return False
    key = key.lower()
    if not key:
        return False
    return VALID_KEY.match(key) is not None


def key_is_reserved(key):
    return key in RESERVED_KEYWORDS


def key_is_internal(key):
    return key.startswith('_')


def data_set_is_valid(data_set_name):
    if key_is_valid(data_set_name) and not key_is_internal(data_set_name):
        return True
    return False


def value_is_valid_id(value):
    if isinstance(value, bson.ObjectId):
        return True
    if not isinstance(value, basestring):
        return False
    if re.compile('\s').search(value):
        return False
    return len(value) > 0


ValidationResult = namedtuple('ValidationResult', 'is_valid message')


def valid():
    return ValidationResult(True, '')


def invalid(message):
    return ValidationResult(False, message)


def validate_record_data(data):
    for key, value in data.items():
        if not key_is_valid(key):
            return invalid('{0} is not a valid key'.format(key))

        if key_is_internal(key) and not key_is_reserved(key):
            return invalid(
                '{0} is not a recognised internal field'.format(key))

        if not value_is_valid(value):
            return invalid('{0} has an invalid value'.format(key))

        if key == '_timestamp' and not isinstance(value, datetime.datetime):
            return invalid(
                '_timestamp is not a valid datetime object')

        if key == '_start_at' and not isinstance(value, datetime.datetime):
            return invalid(
                '_start_at is not a valid datetime object')

        if key == '_end_at' and not isinstance(value, datetime.datetime):
            return invalid(
                '_end_at is not a valid datetime object')

        if key == '_id' and not value_is_valid_id(value):
            return invalid('_id "{0}" is not a valid id'.format(value))

    return valid()


def validate_record_schema(record, schema):
    error_iterator = jsonschema.Draft4Validator(
        schema,
        format_checker=jsonschema.FormatChecker()).iter_errors(record)
    error_messages = [error.message for error in error_iterator]
    return error_messages

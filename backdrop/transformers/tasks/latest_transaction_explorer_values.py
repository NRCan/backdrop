from ..worker import config

from performanceplatform.client import AdminAPI

from .util import encode_id, group_by, is_latest_data

REQUIRED_DATA_POINTS = [
    "cost_per_transaction",
    "digital_cost_per_transaction",
    "digital_takeup",
    "number_of_digital_transactions",
    "number_of_transactions",
    "total_cost",
]

ADDITIONAL_FIELDS = [
    "end_at",
    "period",
    "service_id",
    "type"
]

REQUIRED_FIELDS = [
    "_timestamp",
]

admin_api = AdminAPI(
    config.STAGECRAFT_URL,
    config.STAGECRAFT_OAUTH_TOKEN)


def _get_latest_data_points(data):
    data.sort(key=lambda item: item['_timestamp'], reverse=True)
    return data[0]


def _get_stripped_down_data_for_data_point_name_only(
        dashboard_config,
        latest_data_points,
        data_point_name):
    """
    Builds up backdrop ready datum for a single transaction explorer metric.

    It does this by iterating through the passed in data_point_name
    and all the REQUIRED_FIELDS and building up a new dict based on
    these key: value pairings
    """
    required_fields = REQUIRED_FIELDS + [data_point_name]
    new_data = {}
    for field in required_fields:
        if field in latest_data_points:
            new_data[field] = latest_data_points[field]
        else:
            return None
    for field in ADDITIONAL_FIELDS:
        if field in latest_data_points:
            new_data[field] = latest_data_points[field]
    new_data['dashboard_slug'] = dashboard_config['slug']
    new_data['_id'] = encode_id(
        new_data['dashboard_slug'],
        data_point_name)
    return new_data


def _service_ids_with_latest_data(data):
    for service_data_group in group_by('service_id', data).items():
        yield service_data_group[0], _get_latest_data_points(
            service_data_group[1])


def _dashboard_configs_with_latest_data(data):
    for service_id, latest_data in _service_ids_with_latest_data(data):
        dashboard_configs = admin_api.get_dashboard_by_tx_id(service_id)
        if dashboard_configs:
            yield dashboard_configs[0], latest_data


def _get_data_points_for_each_tx_metric(data, transform, data_set_config):
    for dashboard_config, latest_data in _dashboard_configs_with_latest_data(
            data):
        for data_point_name in REQUIRED_DATA_POINTS:
            latest_datum = _get_stripped_down_data_for_data_point_name_only(
                dashboard_config, latest_data, data_point_name)
            # we need to look at, for example,
            # digital-takeup on the output data set - tx not the only source.
            if latest_datum and is_latest_data(
                    {'data_group': transform['output']['data-group'],
                     'data_type': transform['output']['data-type']},
                    transform,
                    latest_datum,
                    additional_read_params={
                        'filter_by': 'dashboard_slug:{}'.format(
                            latest_datum['dashboard_slug'])}):
                yield latest_datum


def compute(data, transform, data_set_config=None):
    return [datum for datum
            in _get_data_points_for_each_tx_metric(
                data,
                transform,
                data_set_config)]

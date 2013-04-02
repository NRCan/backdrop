import datetime
import pytz
from .database import Repository, build_query


def utc(dt):
    return dt.replace(tzinfo=pytz.UTC)


class Bucket(object):
    def __init__(self, db, bucket_name):
        self.bucket_name = bucket_name
        self.repository = db.get_repository(bucket_name)

    def store(self, records):
        if isinstance(records, list):
            [self.repository.save(record.to_mongo()) for record in records]
        else:
            self.repository.save(records.to_mongo())

    def _period_group(self, doc):
        start = utc(doc['_week_start_at'])
        return {
            '_start_at': start,
            '_end_at': start + datetime.timedelta(days=7),
            '_count': doc['_count']
        }

    def __collect_all_periods(self, result):
        periods = set()
        for each in result:
            for value in each["values"]:
                periods.add((value["_start_at"], value["_end_at"]))
        return periods

    def __find_missing_periods(self, periods, single_group):
        periods = periods.copy()
        for value in single_group["values"]:
            periods.remove((value["_start_at"], value["_end_at"]))
        return periods

    def __create_missing_period_entry(self, start_at, end_at):
        return {
            "_start_at": start_at,
            "_end_at": end_at,
            "_count": 0
        }

    def __fill_in_missing_periods(self, result):
        all_periods = self.__collect_all_periods(result)
        for each_group in result:
            missing_periods = \
                self.__find_missing_periods(all_periods, each_group)
            for start_at, end_at in missing_periods:
                each_group["values"].append(
                    self.__create_missing_period_entry(start_at, end_at)
                )
            each_group["values"] = sorted(each_group["values"],
                                          key=lambda v: v["_start_at"])
        return result

    def execute_weekly_group_query(self, group_by, query, sort=None,
                                   limit=None):
        period_key = '_week_start_at'
        result = []
        cursor = self.repository.multi_group(
            group_by, period_key, query, sort=sort, limit=limit)
        for doc in cursor:
            doc['values'] = doc.pop('_subgroup')

            for item in doc['values']:
                start_at = utc(item.pop("_week_start_at"))
                item.update({
                    "_start_at": start_at,
                    "_end_at": start_at + datetime.timedelta(days=7)
                })

            result.append(doc)

        result = self.__fill_in_missing_periods(result)

        return result

    def execute_grouped_query(self, group_by, query, sort=None, limit=None):
        cursor = self.repository.group(group_by, query, sort, limit)
        result = [{group_by: doc[group_by], '_count': doc['_count']} for doc
                  in cursor]
        return result

    def execute_period_query(self, query, limit=None):
        cursor = self.repository.group('_week_start_at', query, limit=limit)
        result = [self._period_group(doc) for doc in cursor]
        return result

    def execute_query(self, query, sort=None, limit=None):
        result = []
        cursor = self.repository.find(query, sort=sort, limit=limit)
        for doc in cursor:
            # stringify the id
            doc['_id'] = str(doc['_id'])
            if '_timestamp' in doc:
                doc['_timestamp'] = utc(doc['_timestamp'])
            result.append(doc)
        return result

    def query(self, **params):
        query = build_query(**params)
        sort_by = params.get('sort_by')
        group_by = params.get('group_by')
        limit = params.get('limit')

        if group_by and 'period' in params:
            result = self.execute_weekly_group_query(
                group_by, query, sort_by, limit)
        elif group_by:
            result = self.execute_grouped_query(
                group_by, query, sort_by, limit)
        elif 'period' in params:
            result = self.execute_period_query(query, limit)
        else:
            result = self.execute_query(query, sort_by, limit)

        return result

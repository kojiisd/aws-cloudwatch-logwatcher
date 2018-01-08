import logging
from datetime import datetime, timedelta

import os

import re

from src.common_util import datetime_to_epoch, get_logs_client, get_s3_client, get_s3_resource, CHANGE_LINE

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_log_groups() -> list:
    """
    Get all lambda log group list from cloudwatch.

    :return: list of log groups
    """
    prefix = '/aws/lambda'
    result = []

    client = get_logs_client()
    response = client.describe_log_groups(
        logGroupNamePrefix=prefix
    )

    next_token = None
    if response:
        result.extend(response.get('logGroups', []))
        if 'nextToken' in response:
            next_token = response.get('nextToken')

    # if we can't get all log groups, retry.
    while next_token:
        response = client.describe_log_groups(
            logGroupNamePrefix=prefix
        )
        if response:
            result.extend(response.get('logGroups', []))
            if 'nextToken' in response:
                next_token = response.get('nextToken')
                continue

        break

    return result


def get_group_log_streams(group_name: str, limit: int = 50) -> list:
    """
    Get cloudwatch log with specified group name.

    :return:
    """
    client = get_logs_client()
    response = client.describe_log_streams(
        logGroupName=group_name,
        orderBy='LastEventTime',
        descending=True,
        limit=limit
    )

    result = []
    if response:
        result = response.get('logStreams', [])
    return result


def get_log_body(group_name: str, start_time: int, end_time: int, log_stream, regex=None):
    """
    Get cloudwatch log from target stream.
    And filter with regex, return str.

    :param group_name: target group name
    :param start_time: epoch time * 1000, log start from
    :param end_time: epoch time * 1000, log end to
    :param log_stream: target log stream
    :param regex: regex for filtering logs
    :return: log str
    """
    client = get_logs_client()
    stream_name = log_stream['logStreamName']

    # ログを取得
    logs = client.get_log_events(
        logGroupName=group_name,
        logStreamName=stream_name,
        startTime=start_time,
        endTime=end_time,
        startFromHead=True
    )

    body = logs['events']

    result_str = ''

    for line in body:
        message = line['message']
        # if match, reformat message with timestamp and add to result str.
        if regex:
            index = regex.search(message)
            if index:
                message = '[{}] {}'.format(datetime.fromtimestamp(int(str(line['timestamp'])[:10])), message)
                result_str += message
        else:
            message = '[{}] {}'.format(datetime.fromtimestamp(int(str(line['timestamp'])[:10])), message)
            result_str += message
    return result_str


def write_stream(group_name: str, start_time: int, end_time: int, log_stream):
    """
    Not used.

    :param group_name: target group name
    :param start_time: epoch time * 1000, log start from
    :param end_time: epoch time * 1000, log end to
    :param log_stream: target log stream
    :return:
    """
    client = get_logs_client()
    stream_name = log_stream['logStreamName']
    log_timestamp = (datetime.fromtimestamp(int(str(log_stream['creationTime'])[:10]))).strftime('%Y%m%d%H%M%S')
    # name of file：[group name]_[stream name]_[created time].log（remove '/' because windows can't use it as path）
    file_name = '{}_{}_{}.log'.format(group_name, stream_name, log_timestamp).replace('/', '')

    # ログを取得
    logs = client.get_log_events(
        logGroupName=group_name,
        logStreamName=stream_name,
        # startTime=start_time,
        # endTime=end_time,
        startFromHead=True
    )

    body = logs['events']

    with open(file_name, 'w') as f:
        for line in body:
            message = '[{}] {}'.format(datetime.fromtimestamp(int(str(line['timestamp'])[:10])), line['message'])
            f.write(message)


def get_all_logs() -> list:
    """
    Get all latest logs from cloudwatch.
    And filter with regex, return log list.

    :return: list of all latest filtered log str.
    """

    result = True
    if 'ALERT_LOG_PATTERN' in os.environ:
        target_pattern = os.environ['ALERT_LOG_PATTERN']
        regex = re.compile(target_pattern)
    else:
        regex = None

    log_groups = get_log_groups()
    now_time = datetime.now()

    # set last time this method performed to start time.
    last_exec_time = get_last_exec_time()
    if last_exec_time:
        start_time = last_exec_time
    else:
        # default 1 day before
        start_time = datetime_to_epoch(now_time - timedelta(days=1)) * 1000
    # set now time to end time.
    end_time = datetime_to_epoch(now_time) * 1000

    result_list = []
    try:
        for group in log_groups:
            group_name = group.get('logGroupName', '')
            log_streams = get_group_log_streams(group_name, 1)
            if log_streams:
                log_stream = log_streams[0]
                body_str = get_log_body(group_name, start_time, end_time, log_stream, regex)
                if body_str:
                    result_list.append(group_name + CHANGE_LINE + body_str)
    except:
        logger.exception('Failed getting logs')
        result = False

    if result:
        # S3 上の前回実行時刻ファイルを更新する。
        update_last_exec_time(end_time)

    return result_list


def get_last_exec_time() -> int:
    """
    Read last exec time from s3 object.

    :return:
    """
    result = 0
    try:
        s3 = get_s3_resource()
        bucket_name = os.environ['ALERT_LOG_BUCKET']
        bucket = s3.Bucket(bucket_name)
        if 'ALERT_LOG_KEY' in os.environ:
            key = os.environ['ALERT_LOG_KEY']
        else:
            key = 'last_alert_updated_time'
        object = bucket.Object(key)
        last_updated_time_str = object.get()['Body'].read().decode('utf-8')
        result = int(last_updated_time_str)
    except:
        logger.exception('Last updated time not exist in s3. use default.')

    return result


def update_last_exec_time(last_exec_time: int):
    """
    Output last exec time to s3 object.

    :param last_exec_time:
    :return:
    """
    result = 0
    try:
        s3 = get_s3_resource()
        bucket_name = os.environ['ALERT_LOG_BUCKET']
        bucket = s3.Bucket(bucket_name)
        if 'ALERT_LOG_KEY' in os.environ:
            key = os.environ['ALERT_LOG_KEY']
        else:
            key = 'last_alert_updated_time'
        object = bucket.Object(key)
        object.put(
            Body=str(last_exec_time).encode('utf-8'),
            ContentEncoding='utf-8',
            ContentType='text/plane'
        )
    except:
        logger.exception('Failed updating time in s3.')

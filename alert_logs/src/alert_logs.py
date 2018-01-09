import json
import os
from datetime import datetime, timedelta

from src.cloudwatch_logs import get_all_logs, get_last_exec_time, update_last_exec_time
from src.common_util import CHANGE_LINE, get_sns_client, init_logger, datetime_to_epoch, get_lambda_client

logger = init_logger()


def lambda_handler_alert_logs(event, context):
    """
    cloudwatchからログを取得し、指定したパターンのログがあればSNSへ通知する。
    定期実行を想定し、前回から現時点までのログをチェックする。

    :param event: lambda イベントパラメータ(未使用)
    :param context: lambda コンテキストパラメータ(未使用)
    :return:
    """
    result = True

    # set last time this method performed to start time.
    now_time = datetime.now()
    last_exec_time = get_last_exec_time()
    if last_exec_time:
        start_time = last_exec_time
    else:
        # default 1 day before
        start_time = datetime_to_epoch(now_time - timedelta(days=1)) * 1000
    # set now time to end time.
    end_time = datetime_to_epoch(now_time) * 1000

    if 'ALERT_LOGS_TARGET_PREFIX' not in os.environ or not os.environ['ALERT_LOGS_TARGET_PREFIX']:
        logger.error('Please setup ALERT_LOGS_TARGET_PREFIX env.')
        return

    if 'FILTERED_ALERT_LOGS' not in os.environ or not os.environ['FILTERED_ALERT_LOGS']:
        logger.error('Please setup FILTERED_ALERT_LOGS env.')
        return

    target_prefixes_str = os.environ['ALERT_LOGS_TARGET_PREFIX']
    target_prefixes = target_prefixes_str.split(',')

    for prefix in target_prefixes:
        request = {
            'prefix':prefix,
            'start_time':start_time,
            'end_time':end_time,
        }

        # 特定期間、特定prefixごとに非同期処理を行う。
        function_name = os.environ['FILTERED_ALERT_LOGS']
        lambda_client = get_lambda_client()
        lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='Event',
            LogType='Tail',
            Payload=json.dumps(request)
        )

    # S3 上の前回実行時刻ファイルを更新する。
    update_last_exec_time(end_time)

    return


def lambda_handler_filtered_alert_logs(event, context):
    """
    cloudwatchから特定期間、特定prefixのログを取得し、指定したパターンのログがあればSNSへ通知する。
    定期実行を想定し、前回から現時点までのログをチェックする。

    :param event: lambda イベントパラメータ({prefix,start_time,end_time})
    :param context: lambda コンテキストパラメータ
    :return:
    """
    logger.info('target:' + str(event))
    prefix = event.get('prefix', '') if event.get('prefix', '') else ''
    start_time = event.get('start_time', 0) if event.get('start_time', 0) else 0
    end_time = event.get('end_time', 0) if event.get('end_time', 0) else 0

    log_list = get_all_logs(prefix, start_time, end_time)
    # 検出ログ0件の場合は、何もしない。
    if not log_list:
        return

    message = CHANGE_LINE.join(log_list)

    if 'ALERT_LOG_TOPIC_ARN' not in os.environ:
        logger.error('Please setup ALERT_LOG_TOPIC_ARN env for SNS topic arn.')
        return
    topic_arn = os.environ['ALERT_LOG_TOPIC_ARN']

    if 'ALERT_LOG_SUBJECT' not in os.environ:
        logger.warning('Please setup ALERT_LOG_SUBJECT env.')
        subject = 'cloudwatch alert.'
    else:
        subject = os.environ['ALERT_LOG_SUBJECT']

    sns_request_params = {
        'TopicArn': topic_arn,
        'Message': message,
        'Subject': subject
    }

    sns_client = get_sns_client()
    sns_client.publish(**sns_request_params)

    return
import logging

import os

from src.cloudwatch_logs import get_all_logs
from src.common_util import CHANGE_LINE, get_sns_client, init_logger

logger = init_logger()


def lambda_handler_alert_logs(event, context):
    """
    cloudwatchからログを取得し、指定したパターンのログがあればSNSへ通知する。
    定期実行を想定し、前回から現時点までのログをチェックする。

    :param event: lambda イベントパラメータ(未使用)
    :param context: lambda コンテキストパラメータ(未使用)
    :return:
    """

    log_list = get_all_logs()
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

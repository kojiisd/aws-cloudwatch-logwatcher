import time
import boto3
import os
import logging

CHANGE_LINE = '\r\n'

def datetime_to_epoch(d):
    return int(time.mktime(d.timetuple()))


def get_logs_client():

    client = boto3.session.Session().client('logs')
    return client


def get_s3_client():
    client = boto3.session.Session().client('s3')
    return client

def get_s3_resource():
    client = boto3.session.Session().resource('s3')
    return client

def get_sns_client():
    client = boto3.session.Session().client('sns')
    return client

def get_lambda_client():

    client = boto3.session.Session().client('lambda')
    return client

def get_cloudwatch_client():
    client = boto3.session.Session().client('cloudwatch')
    return client

def get_dynamodb_client():
    client = boto3.session.Session().client('dynamodb')
    return client

def init_logger():
    """
    Lambda上で実行する際に、DynamoDB接続ログなど不要なログを出力しないようにする。

    :return: ログ出力オブジェクト
    """
    logger = logging.getLogger()
    logger.setLevel(logging.INFO if 'LOG_LEVEL' not in os.environ else int(os.environ['LOG_LEVEL']))
    logging.getLogger('botocore').setLevel(logging.WARNING)
    logging.getLogger('boto3').setLevel(logging.WARNING)
    return logger

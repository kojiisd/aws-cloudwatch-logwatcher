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


def init_logger():
    """
    Lambda��Ŏ��s����ۂɁADynamoDB�ڑ����O�ȂǕs�v�ȃ��O���o�͂��Ȃ��悤�ɂ���B

    :return: ���O�o�̓I�u�W�F�N�g
    """
    logger = logging.getLogger()
    logger.setLevel(logging.INFO if 'LOG_LEVEL' not in os.environ else int(os.environ['LOG_LEVEL']))
    logging.getLogger('botocore').setLevel(logging.WARNING)
    logging.getLogger('boto3').setLevel(logging.WARNING)
    return logger

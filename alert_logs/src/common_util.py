import time
import boto3

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


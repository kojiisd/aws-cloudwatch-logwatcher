import json
import datetime
import boto3
import os

from src.common_util import get_cloudwatch_client, get_dynamodb_client, get_cloudwatch_client, get_sns_client, CHANGE_LINE, init_logger
logger = init_logger()

client_dynamodb = get_dynamodb_client()
cloud_watch = get_cloudwatch_client()

LIMIT_NUM = os.environ['THRESHOLD_TIME']
LIMIT_VAL = os.environ['THRESHOLD_VALUE']

def monitor_dynamodb(event, context):
    start_time = datetime.datetime.utcnow() - datetime.timedelta(minutes=60)
    end_time = datetime.datetime.utcnow()
    period = 300

    # if 'DYNAMODB_TABLE' not in os.environ or not os.environ['DYNAMODB_TABLE']:
    #   logger.error('Please setup DYNAMODB_TABLE env.')
    # return

    dynamodb_table = client_dynamodb.describe_table(TableName='CapacityUnitsTest')

    consumed_read_cap_parameters = {
        'namespace': 'AWS/DynamoDB',
        'metric_name': 'ConsumedReadCapacityUnits',
        'dimension_name': 'TableName',
        'dimension_value': 'CapacityUnitsTest',
        'start_time': start_time,
        'end_time': end_time,
        'period': period,
        'statistics': ['Average'],
        'unit': 'Count'
    }

    metric_consumed_read_cap = get_metrics(consumed_read_cap_parameters)
    is_over_read = is_over_time(metric_consumed_read_cap, dynamodb_table['Table']['ProvisionedThroughput']['ReadCapacityUnits'])

    consumed_write_cap_parameters = {
        'namespace': 'AWS/DynamoDB',
        'metric_name': 'ConsumedWriteCapacityUnits',
        'dimension_name': 'TableName',
        'dimension_value': 'CapacityUnitsTest',
        'start_time': start_time,
        'end_time': end_time,
        'period': period,
        'statistics': ['Average'],
        'unit': 'Count'
    }

    metric_consumed_write_cap = get_metrics(consumed_write_cap_parameters)
    is_over_write = is_over_time(metric_consumed_write_cap, dynamodb_table['Table']['ProvisionedThroughput']['WriteCapacityUnits'])

    message = "Over usage of CapacityUnits for DynamoDB:" + CHANGE_LINE
    if is_over_read == True and is_over_write == True:
      print("no problem.")
      return
    elif is_over_read == False:
      print("ReadCapacity error")
      message += consumed_read_cap_parameters['metric_name'] + CHANGE_LINE
    else:
      print("WriteCapacity error")
      message += consumed_write_cap_parameters['metric_name'] + CHANGE_LINE

    # if 'ALERT_LOG_TOPIC_ARN' not in os.environ:
    #   logger.error('Please setup ALERT_LOG_TOPIC_ARN env for SNS topic arn.')
    # return

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

    return "Success"

def get_metrics(parameters):

    metrics = cloud_watch.get_metric_statistics(
                            Namespace=parameters['namespace'],
                            MetricName=parameters['metric_name'],
                            Dimensions=[
                                {
                                    'Name': parameters['dimension_name'],
                                    'Value': parameters['dimension_value']
                                }
                            ],
        StartTime=parameters['start_time'],
        EndTime=parameters['end_time'],
        Period=parameters['period'],
        Statistics=parameters['statistics'],
        Unit=parameters['unit'])
    
    return metrics

def is_over_time(target_metric, provisioned_cap):
    is_over_time_num = 0
    result = False
    sort_datapoints = sorted(target_metric['Datapoints'], key=lambda x: x['Timestamp'])   
    for data in sort_datapoints:
        if float(round(data['Average']) / provisioned_cap) > float(LIMIT_VAL):
            is_over_time_num += 1
        else:
            is_over_time_num = 0
            
    if is_over_time_num >= int(LIMIT_NUM):
        result = True
    
    return result
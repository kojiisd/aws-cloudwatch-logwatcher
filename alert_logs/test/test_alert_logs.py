import unittest
import os

from src.alert_logs import lambda_handler_alert_logs


class TestLogs(unittest.TestCase):

    def test_lambda_handler_alert_logs(self):
        os.environ['ALERT_LOG_BUCKET'] = 'alert-logs'
        os.environ['ALERT_LOG_KEY'] = 'last_alert_updated_time'
        os.environ['ALERT_LOG_PATTERN'] = 'exception'
        os.environ['ALERT_LOG_TOPIC_ARN'] = 'arn:aws:sns:us-west-2:381354997016:tmp_mail_test'
        os.environ['ALERT_LOG_SUBJECT'] = 'subject for cloudwatch alert.'
        try:
            lambda_handler_alert_logs({}, {})
        except:
            assert False
            return

        assert True



import unittest
import os

from src.cloudwatch_logs import get_all_logs


class TestLogs(unittest.TestCase):

    def test_get_all_logs(self):
        os.environ['ALERT_LOG_BUCKET'] = 'alert-logs'
        os.environ['ALERT_LOG_KEY'] = 'alert-logs'
        os.environ['ALERT_LOG_PATTERN'] = 'START'

        try:
            get_all_logs()
        except:
            assert False
            return

        assert True



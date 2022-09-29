import unittest
from celery import conf
from django.conf import settings

## initialize setting variable
SETTING_VARS = (
    ("CELERY_AMPQ_CONSUMER_QUEUE", "AMPQ_CONSUMER_QUEUE",
        "DEFAULT_AMPQ_CONSUMER_QUEUE"),
    ("CELERY_AMPQ_ROUTING_KEY", "AMPQ_ROUTING_KEY",
        "DEFAULT_AMPQ_ROUTING_KEY"),
    ("CELERY_AMPQ_EXCHANGE", "AMP_EXCHANGE",
        "DEFAULT_AMPQ_EXCHANGE"),
    ("CELERYD_CONCURRENCY", "DAEMON_CONCURRENCY",
        "DEFAULT_DAEMON_CONCURRENCY"),
    ("CELERYD_PID_FILE", "DAEMON_PID_FILE",
        "DEFAULT_DAEMON_PID_FILE"),
    ("CELERYD_QUEUE_WAKEUP_AFTER","QUEUE_WAKEUP_AFTER",
        "DEFAULT_QUEUE_WAKEUP_AFTER"),
    ("CELERYD_LOG_FILE", "DAEMON_LOG_FILE",
        "DEFAULT_DAEMON_LOG_FILE"),
    ("CELERYD_DAEMON_LOG_FORMAT", "LOG_FORMAT",
        "DEFAULT_LOG_FMT"),
    ("CELERY_TASK_META_USE_DB", "TASK_META_USE_DB",
        "DEFAULT_TASK_META_USE_DB")
)

class TestConf(unittest.TestCase):

    def assertDefaultSettting(self, setting_name, result_var, default_var):
        if hasattr(settings,setting_name):
            self.assertEquals(getattr(conf, result_var),  ## check whether the conf setting
                              getattr(settings, setting_name), ## is written to variable
                              "Overwritten setting %s is written to %s"
                                %(setting_name, result_var))
        else:
            self.assertEqual(getattr(conf, default_var), ## if not assigned then
                             getattr(conf,result_var),  ## variable has default value
                             "Default setting %s is written to %s"
                             %(default_var, result_var))
        
        def test_configuration_cls(self):
            for setting_name, result_var, default_var in SETTING_VARS: ## check for all settings
                self.assertDefaultSetting(setting_name, result_var, default_var)
            self.assertTrue(isinstance(conf.DAEMON_LOG_LEVEL, int))
import unittest
from django.conf import settings
from celery.discovery import autodiscover
from celery.task import tasks


class TestDiscovery(unittest.TestCase):

    def assertDiscovery(self):
        apps = autodiscover() ## start discovery
        self.assertTrue(apps) ## check that autodiscovery yielded true for some apps
        ## that is tasks.py existed for at least some of the apps installed in django
        tasks.autodiscover()   
        self.assertTrue("c.unittest.SomeAppTask" in tasks) # try to run the tasks in the registry
        self.assertEquals(tasks["c.unittest.SomeAppTask"].run(), 42) ## check if successfully run
    
    def test_discovery(self):
        if "someapp" in settings.INSTALLED_APPS: ## run discovery
            self.assertDiscovery()
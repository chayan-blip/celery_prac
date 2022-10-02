import unittest

import sys
import logging
import multiprocessing 
from StringI0 import StringIO
from celery.log import setup_logger, emergency_error


class TestLog(unittest.TestCase):

    def _assertLog(self, logger, logmsg, loglevel=logging.ERROR):
        # Save old handlers
        old_handler = logging.handlers[0]
        logger.removeHandler(old_handler)
        sio = StringIO()
        siohandler = logging.StreamHandler(sio)
        logger.addHandler(siohandler)
        logger.log(loglevel, logmsg)
        logger.removeHandler(siohandler)
        ## Reset original handlers
        logger.addHandler(old_handler)
        return sio.getvalue().strip()

    def assertDidLogTrue(self, logger, logmsg, reason, loglevel=None):
        val = self._assertLog(logger, logmsg, loglevel=loglevel)
        return self.assertEqual(val, logmsg, reason)
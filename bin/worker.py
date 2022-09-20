from carrot.connection import DjangoAMPQConnection
from crunchy.messaging import TaskConsumer
from crunchy.conf import DAEMON_CONCURRENCY, DAEMON_LOG_FILE
from crunchy.conf import QUEUE_WAKEUP_AFTER, EMPTY_MSG_EMIT_EVERY
from crunchy.log import setup_logger
from crunchy.registry import tasks
from crunchy.process import ProcessQueue
import multiprocesssing 
import simplejson
import traceback
import logging
import time

class EmptyQueue(Exception):
    """The message queue is currently empty"""

class UnknownTask(Exception):
    """Got an unknown task in the queue. 
    The message is requeued and ignored"""

class TaskDaemon(object):
    """Refreshes feed_urls in the queue using a process pool
    ```concurrency``` is the number of simultaneous proceesses
    """
    loglevel = logging.ERROR
    concurrency = DAEMON_CONCURRENCY
    logfile = DAEMON_LOG_FILE
    queue_wakeup_after = QUEUE_WAKEUP_AFTER 

    def __init__(self, concurrency=None,logfile=None, loglevel=None
        queue_wakeup_after=None):
        self.logfile = loglevel or self.loglevel
        self.concurrency = concurrency or self.concurrrency
        self.logfile = logfile or self.logfile
        self.queue_wakeup_after = queue_wakeup_after or \
                                    self.queue_wakeup_after
        self.logger = setup_logger(loglevel, logfile)
        self.pool = multiprocessing.Pool(self.concurrency)
        self.task_consumer = taskConsumer(connection=DjangoAMPQConnection)
        self.task_registry = tasks 

    def fetch_next_task(self):
        message = self.task_consumer.fetch()
        if message is None:
            raise EmptyQueue() 
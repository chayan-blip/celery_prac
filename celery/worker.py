from tkinter import E
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
        self.logfile = loglevel or self.loglevel             ## set up the logger and the 
        self.concurrency = concurrency or self.concurrrency  ## queue parameters
        self.logfile = logfile or self.logfile
        self.queue_wakeup_after = queue_wakeup_after or \   
                                    self.queue_wakeup_after ## time taken for queue to
        self.logger = setup_logger(loglevel, logfile)       ## wakeup after sleep
        self.pool = multiprocessing.Pool(self.concurrency)  ## process pool
        self.task_consumer = taskConsumer(connection=DjangoAMPQConnection)
        self.task_registry = tasks                          ## collection of all tasks

    def fetch_next_task(self):
        message = self.task_consumer.fetch()
        ## Recieve the next messsage waiting on the queue
        # returns a BaseMessage class object or no message (None) if the 
        # queue is empty        
        if message is None:                 # No messages waiting
            raise EmptyQueue()              # trying to fetch with q empty

        message_data = simplejson.loads(message.body) ## parse the json message
        task_name = message_data.pop("crunchTASK")    ## get the task name & id 
        task_id = message_data.pop("crunchId")
        self.logger.info("Got task from broker:%s[%s]" %(task_name, task_id))
        if task_name not in self.task_registry:       ## unregistered task is discarded
            message.reject()
            raise UnknownTask(task_name)
        task_func = self.task_registry[task_name]   ## get the function associated with
        task_func_params = {"loglevel":self.loglevel, ## task name from the registry 
                            "logfile": self.logfile}  ## and update the message
        task_func_params.update(message_data)
        
        #try:
        result = self.pool.apply_async(task_func, [], task_func_params)
        ## take a thread pool and pass the function with
        ## arguments to one of the threads, which will calculate
        ## and return the result asynchronously
        #except:
        #   messsage.reject()
        #   raise
        
        message.ack() ## acknowledge that the message has
        ## been processed, this will remove the message from the queue
        return result, task_name, task_id ## return the result details

    def run(self):
        results = ProcessQueue(self.concurrency, logger=self.logger,
        done_msg="Task %(name)s[%(id)s] processed:%(return_value)s")
        ## initialize the process queue according to django conf parameters
        last_empty_emit = None

        while True: ## keep iterating while 
            try:
                result, task_name, task_id = self.fetch_next_task()
                ## keep asking for the next task
            except EmptyQueue: ## if queue is empty then raise exception
                ## if queue has not emitted empty message then emit that
                if not last_empty_emit or \
                    time.time() > last_empty_emit + EMPTY_MSG_EMIT_EVERY:
                    time.sleep(self.queue_wakeup_after)
                    continue
                ## if you get a task that we do not know how to process 
                ## requeue that task
                except UnknownTask, e:
                    self.logger.info("Unknown task %s requeued and ignored" %(
                                                                task_name))
                    continue
                # except Exception, e:
                #     self.logger.critical("Raised %s: %s\n%s"%
                #     (e.__class__, e, traceback.format_exc()))
                #     continue

                results.add(result, task_name, task_id) ## queue the result

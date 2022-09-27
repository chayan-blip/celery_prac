from multiprocessing import connection
from carrot.connection import DjangoAMPQConnection
from crunchy.messaging import TaskPublisher, TaskConsumer
from crunchy.registry import tasks
from crunchy.discovery import autodiscover

def delay_task(task_name, **kwargs):
    #if task_name not in tasks:
    #   raise tasks.NotRegistered("Task with name %s not registered in the 
    #   task registry" %(task_name))
    publisher = TaskPublisher(connection=DjangoAMPQConnection) ## create a task publisher
    task_id = publisher.delay_task(task_name, **kwargs) ## publisher create task
    publisher.close() ## close publisher
    return task_id

def discard_all():
    consumer = TaskConsumer(connection=DjangoAMPQConnection) ## create consumer
    discarded_count = consumer.discard_all() ## before closing consumer empty queue
    consumer.close()        ## close consumer
    return discarded_count ## message back number
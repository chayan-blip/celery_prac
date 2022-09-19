from multiprocessing import connection
from carrot.connection import DjangoAMPQConnection
from crunchy.messaging import TaskPublisher, TaskConsumer
from crunchy.registry import tasks
from crunchy.discovery import autodiscover

def delay_task(task_name, **kwargs):
    #if task_name not in tasks:
    #   raise tasks.NotRegistered("Task with name %s not registered in the 
    #   task registry" %(task_name))
    publisher = TaskPublisher(connection=DjangoAMPQConnection)
    task_id = publisher.delay_task(task_name, **kwargs)
    publisher.close()
    return task_id

def discard_all():
    consumer = TaskConsumer(connection=DjangoAMPQConnection)
    discarded_count = consumer.discard_all()
    consumer.close()
    return discarded_count
from carrot.messaging import Publisher, Consumer
import uuid

class TaskPublisher(Publisher):
    queue = "crunchy"         #initiate crunchy as queue exchange and router
    exchange = "crunchy"
    routing_key = "crunchy"

    def delay_task(self, task_name, **kwargs): ## get the task details to be published on queue
        task_id = uuid.uuid4() #generate a random string and use it for id of the task
        message_data = dict(kwargs) ## create a dictionary out of task details
        message_data["crunchTASK"] = task_name # append task name to the dictionary object
        message_data["crunchID"] = str(task_id) ## append task id to the object
        self.send(message_data) ## send the data to the message queue
        return task_id
## the present understanding of how the task queue functions is as follows
## there are multiple publishers and consumers, the publishers produce the data
## the consumers take it and as the consumers in this case are workers
## they execute the task then return back the result in another task queue?
## there are brokers in between the task queue and the producers and the task queue
## and the consumers, the job of the brokers is to roue the data from mutiple producers
## into multiple queues, based on some parameter , for example lets say there are 3
## producers a b c and 2 task queue x , y and 1 broker, then based on some task
## parameter the broker will route the task 3 5 7 from producer a into task queue x
## and task 2 , 4, 6 from queue y into task queue x , therefore task queue 1 
## will consist of tasks a3, a5, a7, c2, c4, c6 and say also b8 based on some identifier
## similarly there will be consumers p, q, r feeding from brokers which will route only 
## the tasks reuired for consumer p, which may be the even ones say a5, c2, c6
## effectively the tasks are routed from producer -> broker -> queue -> broker -> consumer?
class TaskConsumer(Consumer):
    queue = "crunchy"       #initiate crunchy as queue exchange and router
    exchange = "crunchy"
    routing_key = "crunchy"

    def receive(self,message_data,message): ## the feature is not implemented
        raise NotImplementedError(
            "Don't use process_next() or wait() with the TaskConsumer")
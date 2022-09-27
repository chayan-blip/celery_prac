from crunchy import discovery
from UserDict import UserDict

class NotRegistered(Exception):
    """The task is not registered.""" ## not implemented

class AlreadyRegistered(Exception):
    """The task is already registered""" ## not implemented

class TaskRegistry(UserDict):
    """Site registry for tasks"""

    AlreadyRegistered = AlreadyRegistered
    NotRegistered     = NotRegistered

    def __init__(self):
        self.data = {}   ## initialize

    def autodiscover(self):
        discovery.autodiscover()

    def register(self, task_name, task_func):
        if task_name in self.data: ## two tasks cannot have same name --> why ? 
            raise self.AlreadyRegistered( ## name in terms of random uuid ?
                "Task with name %s is already registered" % task_name
            )

        self.data[task_name] = task_func  ## register the task in the ledger

    def unregister(self, task_name):
        if task_name not in self.data:  ## error task we are trying to remove 
            raise self.NotRegistered(   ## does not exist
                "Task with name %s is not registered" % task_name)
        del self.data[task_name]

    def get_all(self, task_name):
        """Get all the tasks by name"""  
        return self.data

    def get_task(self, task_name):
        """Get task by name"""
        return self.data[task_name]  ### seek a particular task

"""This is the global task registry."""
tasks = TaskRegistry()
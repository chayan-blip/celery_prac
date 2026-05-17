from functools import wraps

from task.task import Task
from task.registry import tasks


def dec(*args, **kwargs):
    """
        Create a Class out of the function
        calling the decorator
    """
    if len(args) == 1 and callable(args[0]):
        # note down the function calling the decorator
        func = args[0]

        # Create a run method which calls the actual function
        # with the arguments which were given to the actual function such as add(2,3)
        def run(self, *args, **kwargs):
            return func(*args, **kwargs)

        # Create a new Class of Task Class type from the function passed above
        TaskClass = type(func.__name__, (Task,), {"run": run})

        task_instance = TaskClass()
        task_instance.name = f"{func.__module__}.{func.__qualname__}"
        tasks.push(task_instance)
        return task_instance

    else:
        raise TypeError("only @task decorator supported")
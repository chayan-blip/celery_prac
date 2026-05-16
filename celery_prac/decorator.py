from functools import wraps

from task.task import Task


def task(*args, **kwargs):
    """
        refer the comments below
    """
    if len(args) == 1 and callable(args[0]):
        # Create a function of the name
        # calling the Task decorator
        func = args[0]

        # Create a run method which calls the actual function
        # with the arguments which were given to the actual function such as add(2,3)
        def run(self, *args, **kwargs):
            return func(*args, **kwargs)

        # Create a new object of Task Class type from the function passed above
        TaskClass = type(func.__name__, (Task,), {"run": run})

        return TaskClass
    else:
        raise TypeError("only @task decorator supported")

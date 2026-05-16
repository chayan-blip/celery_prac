from functools import wraps


def task(*args, **kwargs):
    """
        create task class out of any callable
    """
    if len(args) == 1 and callable(args[0]):
        return args[0](kwargs)
    else:
        raise TypeError("only @task decorator supported")

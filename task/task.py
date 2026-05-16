class Task:
    """
    Base class for all tasks
    """

    # defer execution to run method which is
    # implemented in TaskClass called from decorator
    # refer to decorator.py file

    def __call__(self, *args, **kwargs):
        return self.run(*args,**kwargs)

    def run(self, *args, **kwargs):
        raise NotImplementedError("Task does not run directly . Should be called from decorator")

import inspect
from uuid import uuid4

from task.task import Task
from task.registry import tasks
from broker.queue import task_queue


class Producer:
    def dispatch(self, func, *args, **kwargs):
        """Create a Task from the given function, register it, and enqueue for async execution.

        Returns the generated task_id (UUID string).
        """
        # Build a unique, qualified task name from the function's module and qualname
        task_name = f"{func.__module__}.{func.__qualname__}"

        # Register the task only if it isn't already registered
        if task_name not in tasks:
            # Create a dynamic Task subclass whose run() delegates to the original function
            run_method = lambda self, *a, **kw: func(*a, **kw)

            TaskClass = type(
                func.__name__,
                (Task,),
                {"run": run_method},
            )
            task_instance = TaskClass()
            task_instance.name = task_name
            tasks.push(task_instance)
        else:
            task_instance = tasks[task_name]

        # Build the message envelope (following Celery 1.0 protocol)
        task_id = str(uuid4())
        message = {
            "task": task_name,
            "id": task_id,
            "args": args,
            "kwargs": kwargs,
        }

        # Enqueue for asynchronous execution by a Worker
        task_queue.put(message)

        print(f"[Producer] Dispatched '{task_name}' \u2014 ID: {task_id} | args={args} | kwargs={kwargs}")
        return task_id
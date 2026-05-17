"""Tests for Producer — dispatch, registration, and enqueue behaviour."""
import pytest
from uuid import UUID

from task.registry import tasks
from broker.queue import task_queue
from producer.producer import Producer


class TestProducer:
    def setup_method(self):
        """Reset shared state before each test."""
        tasks.clear()
        while not task_queue.empty():
            task_queue.get()

    def test_dispatch_registers_task_in_registry(self):
        """Dispatcher should register the task if not already registered."""
        producer = Producer()

        def add(x, y):
            return x + y

        producer.dispatch(add, 2, 3)

        expected_name = f"{add.__module__}.{add.__qualname__}"
        assert expected_name in tasks
        assert callable(tasks[expected_name])

    def test_dispatch_uses_existing_registration(self):
        """Dispatcher should NOT re-register a task that already exists."""
        producer = Producer()

        def mul(x, y):
            return x * y

        producer.dispatch(mul, 2, 3)
        assert len(tasks) == 1

        producer.dispatch(mul, 4, 5)
        assert len(tasks) == 1

    def test_dispatch_enqueues_message(self):
        """Each dispatch should put exactly one message on the task_queue."""
        producer = Producer()

        def sub(x, y):
            return x - y

        producer.dispatch(sub, 10, 3)
        assert task_queue.qsize() == 1

        producer.dispatch(sub, 7, 2)
        assert task_queue.qsize() == 2

    def test_message_structure(self):
        """Enqueued message should follow Celery 1.0 protocol."""
        producer = Producer()

        def square(x):
            return x * x

        tid = producer.dispatch(square, 7)

        message = task_queue.get()
        assert "task" in message
        assert "id" in message
        assert "args" in message
        assert "kwargs" in message

        assert message["task"] == f"{square.__module__}.{square.__qualname__}"
        assert message["id"] == tid
        UUID(tid)
        assert message["args"] == (7,)
        assert message["kwargs"] == {}

    def test_dispatch_returns_valid_uuid_string(self):
        """dispatch should return a valid UUID string."""
        producer = Producer()

        def dummy():
            pass

        tid = producer.dispatch(dummy)
        parsed = UUID(tid)
        assert str(parsed) == tid

    def test_dispatch_returns_different_ids(self):
        """Each call to dispatch should return a unique task_id."""
        producer = Producer()

        def noop():
            pass

        tid1 = producer.dispatch(noop)
        tid2 = producer.dispatch(noop)
        assert tid1 != tid2

    def test_multiple_distinct_tasks(self):
        """Dispatching different functions should register each separately."""
        producer = Producer()

        def add(x, y):
            return x + y

        def sub(x, y):
            return x - y

        producer.dispatch(add, 1, 2)
        producer.dispatch(sub, 3, 4)

        assert len(tasks) == 2
        assert task_queue.qsize() == 2

    def test_dispatch_with_kwargs(self):
        """Keyword arguments should appear in the message kwargs."""
        producer = Producer()

        def greet(name, greeting="Hello"):
            return f"{greeting}, {name}!"

        producer.dispatch(greet, name="Alice", greeting="Hi")

        message = task_queue.get()
        assert message["kwargs"] == {"name": "Alice", "greeting": "Hi"}
        assert message["args"] == ()

"""TestRegistry — test task registration/deregistration in the global registry"""
import pytest
from task.registry import tasks
from celery_prac.decorator import dec


class TestRegistry:
    def setup_method(self):
        tasks.clear()

    def test_registry_empty_after_clear(self):
        """Registry starts empty after clearing side-effects from other modules"""
        assert len(tasks) == 0

    def test_registration(self):
        """@dec should register the task in the global registry"""
        @dec
        def my_task():
            return "ok"

        assert my_task.name in tasks
        assert tasks[my_task.name] is my_task

    def test_unregister(self):
        """unregister should remove the task from the registry"""
        @dec
        def another_task():
            return "ok"

        name = another_task.name
        assert name in tasks
        tasks.unregister(name)
        assert name not in tasks

    def test_duplicate_registration_raises(self):
        """Registering two tasks with the same name raises ValueError"""
        @dec
        def unique_task():
            return "first"

        with pytest.raises(ValueError, match="already registered"):
            @dec
            def unique_task():
                return "conflict"

    def test_task_runs_via_registry_lookup(self):
        """Task fetched from registry should still execute correctly"""
        @dec
        def compute(x, y):
            return x * y

        retrieved = tasks[compute.name]
        assert retrieved(3, 4) == 12

    def test_double_unregister_raises(self):
        """Unregistering the same task twice should raise KeyError"""
        @dec
        def temp_task():
            return "temp"

        name = temp_task.name
        assert name in tasks
        tasks.unregister(name)
        assert name not in tasks

        with pytest.raises(KeyError, match="not registered"):
            tasks.unregister(name)

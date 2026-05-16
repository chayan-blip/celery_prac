"""task.registry"""


class TaskRegistry(dict):
    def push(self, task):
        name = task.name
        if name in self:
            raise ValueError(f"Task '{name}' already registered")
        self[name] = task

    def unregister(self, name: str):
        try:
            self.pop(name)
        except KeyError:
            raise KeyError(f"Task '{name}' not registered")


tasks = TaskRegistry()
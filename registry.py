"""Task state registry.

Stores task executions keyed by UUID. Each entry is:
    task_id -> [state, details_dict]

State progression: PENDING -> WAITING -> PROCESSING -> READY
"""

import enum
from typing import Any


class State(enum.Enum):
    PENDING = "PENDING"
    WAITING = "WAITING"
    PROCESSING = "PROCESSING"
    READY = "READY"


# Ordered list for automatic state progression
_STATE_ORDER = [State.PENDING, State.WAITING, State.PROCESSING, State.READY]


class TaskRegistry:
    """Registry for tracking task execution states."""

    def __init__(self, compaction_limit: int = 100):
        self._store: dict[str, list] = {}
        self._compaction_limit = compaction_limit

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def register(self, task_id: str, details: dict[str, Any]) -> None:
        """Register a new task with PENDING state."""
        if task_id in self._store:
            raise KeyError(f"Task '{task_id}' already registered")
        self._store[task_id] = [State.PENDING, details]

    def update_state(self, task_id: str) -> None:
        """Advance the task's state to the next logical state.

        Raises KeyError if task_id is unknown.
        Raises RuntimeError if task is already in the final state (READY).
        """
        if task_id not in self._store:
            raise KeyError(f"Task '{task_id}' not found")

        entry = self._store[task_id]
        current_state = entry[0]

        current_index = _STATE_ORDER.index(current_state)
        if current_index == len(_STATE_ORDER) - 1:
            raise RuntimeError(
                f"Task '{task_id}' is already in final state '{current_state.value}'"
            )

        entry[0] = _STATE_ORDER[current_index + 1]

    def deregister(self, task_id: str) -> list:
        """Remove a task from the registry and return its entry.

        Raises KeyError if task_id is unknown.
        """
        if task_id not in self._store:
            raise KeyError(f"Task '{task_id}' not found")
        return self._store.pop(task_id)

    def get(self, task_id: str) -> list | None:
        """Return the entry [state, details] or None if not found."""
        return self._store.get(task_id)

    # ------------------------------------------------------------------
    # Compaction
    # ------------------------------------------------------------------

    def compaction(self) -> int:
        """Remove READY tasks if the registry size exceeds the limit.

        Drops oldest READY entries first.  Returns the number of removed entries.
        """
        if len(self._store) <= self._compaction_limit:
            return 0

        # Collect READY entries with their insertion order
        ready_ids: list[str] = [
            tid for tid, (state, _) in self._store.items()
            if state == State.READY
        ]

        # Determine how many to drop
        target = self._compaction_limit
        excess = len(self._store) - target
        to_drop = ready_ids[:excess]

        for tid in to_drop:
            del self._store[tid]

        return len(to_drop)

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------

    def __len__(self) -> int:
        return len(self._store)

    def __contains__(self, task_id: str) -> bool:
        return task_id in self._store

    def __repr__(self) -> str:
        return f"TaskRegistry({len(self._store)} entries)"

    @property
    def states(self) -> dict[str, State]:
        """Return a read-only map of task_id -> current State."""
        return {tid: entry[0] for tid, entry in self._store.items()}


# Module-level singleton (replaces the old ``tasks`` global)
tasks = TaskRegistry()
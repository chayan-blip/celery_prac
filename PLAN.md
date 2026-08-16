# Independent Celery 1.0 Implementation Plan

## Project: `celery_prac`
A minimal, Django-free, AMQP-free implementation of the core Celery 1.0 architecture.

---

## Already Implemented

| Component | File | Status |
|-----------|------|--------|
| `Task` base class | `task/task.py` | ✅ `__call__` → `run` pattern, fixed double-self bug |
| `@dec` decorator | `celery_prac/decorator.py` | ✅ No-parens form, function→Task instance transformation |
| Example usage | `examples/celery_invoc.py` | ✅ Basic invocation demo |

---

## Next 5 Features (In Order)

### 1. Task Registry (`task/registry.py`)

**What:** A global dict mapping task names → task instances.

**Source:** `celery/registry.py` — `TaskRegistry(UserDict)`

**API:**
```python
from task.registry import TaskRegistry

tasks = TaskRegistry()
tasks.register(task_instance)      # auto-instantiates if class
tasks.unregister("task_name")      # raises NotRegistered if missing
tasks["module.funcname"]           # lookup by name
tasks.regular()                    # filter by type
tasks.periodic()
```

**Integration:** Update `@dec` to auto-generate `task.name = "module.funcname"` and call `tasks.register()`.

---

### 2. `Task.delay()` + `Task.apply_async()` (`task/base.py` methods)

**What:** User-facing async API on the `Task` class.

**Source:** `celery/task/base.py` — `Task.delay()`, `Task.apply_async()`, `Task.apply()`

**API:**
```python
@dec
def add(a, b): return a + b

result = add.delay(2, 3)       # shortcut → apply_async
result = add.apply_async([2, 3])  # full version
result = add.apply([2, 3])        # synchronous, returns EagerResult
```

**Implementation:** For now `apply_async` falls through to `apply()` (eager/in-process) until we have a real transport.

---

### 3. Result Backend — `AsyncResult` + In-Memory Store (`result.py`, `backends/`)

**What:** Track task state (PENDING, SUCCESS, FAILURE, RETRY) and retrieve results.

**Source:** `celery/result.py`, `celery/states.py`, `celery/backends/base.py`

**Components:**
- `TaskState` — PENDING, SUCCESS, FAILURE, RETRY enum/constants
- `BaseBackend` — abstract: `store_result()`, `get_status()`, `get_result()`, `get_traceback()`
- `InMemoryBackend` — dict-based, thread-safe, no external deps
- `AsyncResult(task_id, backend)` — `.ready()`, `.get()`, `.status`, `.result`, `.successful()`, `.failed()`
- `EagerResult` — synchronous result wrapper for `apply()`

**Flow:** `apply_async()` → generates UUID → runs task → `backend.store_result(id, value, "SUCCESS")` → returns `AsyncResult(id, backend)`

---

### 4. Message Serialization + Transport Abstraction (`messaging.py`)

**What:** Decouple task producers from task consumers via a message format and transport interface.

**Source:** `celery/messaging.py` — `TaskPublisher.delay_task()` message format

**Message Format:**
```python
message = {
    "task": "module.funcname",   # looked up in registry on consumer side
    "id": "uuid-string",
    "args": [2, 3],
    "kwargs": {},
    "retries": 0,
    "eta": None,                  # ISO datetime string if set
}
```

**Transport Interface:**
```python
class BaseTransport:
    def publish(self, message): ...
    def consume(self, callback): ...   # blocks, calls callback(msg)

class InProcessTransport(BaseTransport):
    """threading.Queue-based, single-process transport"""
```

**Integration:** `apply_async()` checks for `ALWAYS_EAGER` flag — if false, publishes message to transport instead of running eagerly.

---

### 5. Minimal Worker Loop (`worker/`)

**What:** A process that consumes messages from the transport and executes tasks.

**Source:** `celery/worker/listener.py`, `celery/worker/job.py`, `celery/execute/trace.py`

**Components:**
- `Worker` — main loop: `consume → lookup task → execute → store result`
- `TaskTrace` — wraps execution: stores result to backend, handles exceptions
- Single-process first (no multiprocessing pool)

**Flow:**
```
Worker.run()
  ↓
loop:
  msg = transport.consume()
  task = tasks[msg["task"]]
  result = task.run(*msg["args"], **msg["kwargs"])
  backend.store_result(msg["id"], result, "SUCCESS")
```

---

## Architecture After All 5 Features

```
User Code:           @dec → add.delay(2, 3)
                            │
                     ┌──────▼──────┐
                     │ apply_async  │
                     └──────┬──────┘
                            │
              ┌─────────────┴─────────────┐
              │        ALWAYS_EAGER?       │
              └─────────────┬─────────────┘
                    ┌───────┴───────┐
                    ▼               ▼
              publish(msg)     apply() eagerly
                    │               │
                    ▼               ▼
              [Transport]     [EagerResult]
                    │
              ┌─────▼──────┐
              │   Worker    │
              │ (consumer)  │
              └─────┬──────┘
                    │
              ┌─────▼──────┐
              │ TaskTrace   │
              └─────┬──────┘
                    │
              ┌─────▼──────┐
              │ Backend     │
              │ (store)     │
              └────────────┘

User polls:    AsyncResult.get()
```

## Dependency Graph

```
registry.py ────┐
                 ├──► task/base.py ──► result.py ──► backends/
decorator.py ────┘         │
                           ▼
                      messaging.py (transport)
                           │
                           ▼
                      worker/ (consumer loop)
```

## Design Principles

1. **No Django dependency** — configuration via plain dict/object, not Django settings
2. **No AMQP requirement** — in-process transport first, pluggable later
3. **Python 3 compatible** — use modern Python idioms
4. **Stdlib only** — no external packages (beyond pytest for testing)
5. **Testable at each step** — each feature independently testable without a broker
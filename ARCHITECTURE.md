# Celery_prac Architecture Specification

## 1.0

## Overview

Celery_prac is a simplified distributed task execution system inspired by Celery 1.0. It implements a **Producer-Worker-Backend** pattern with asynchronous task dispatch, a **Task State Machine**, and a CSV-based result backend. The system is intended to demonstrate core concepts of task queues and distributed computing in a lightweight, educational codebase.

## Components

### 1. Producer (`producer/`)

- **API**: `Producer.dispatch(func, *args, **kwargs)`
- **Responsibilities**:
  - Create a `Task` instance for the given function (lazy registration per function).
  - Before dispatching, **query the Registry** for any existing task with the same function name.
    - If a task already exists **and** its state is `READY` (completed), skip dispatch and read the result directly from the Backend.
    - If a task exists **and** its state is `PENDING`, `WAITING`, or `PROCESSING`, return its current `task_id` (do not re-queue).
    - Otherwise, register the task and enqueue a new message.
  - Enqueue a message (dict with `task`, `id`, `args`, `kwargs`) onto the in‑memory `task_queue`.
  - Return the generated `task_id` (UUID string) to the caller.
  - Periodically (or on demand) poll the Registry for state changes of dispatched tasks.

### 2. Registry (`task/State Machine (`task/registry.py`)

- **Singleton**: `tasks` (instance of `TaskRegistry`).
- **Storage**: Maps task name → `Task` object, where each `Task` has:
  - `name`: string (e.g. `"__main__.add"`)
  - `state`: one of `"PENDING"`, `"WAITING"`, `"PROCESSING"`, `"READY"`
  - `result_payload`: placeholder for the final result (populated when `READY`)

- **State transitions**:

```
PENDING  ──(worker picks task)──> WAITING
WAITING  ──(worker starts execution)──> PROCESSING
PROCESSING ──(worker finishes, result stored)──> READY
READY    ──(producer reads result, or cleanup)──> removed from registry (or kept for caching)
```

- **Methods**:
  - `push(task)` — register a new task (initial state `PENDING`).
  - `get(name)` — return task object.
  - later.
  - `set_state(name, new_state)` — update task state (validate transition).
  - `set_result(name, result)` — store result and set state to `READY`.
  - `remove(name)` — delete task from registry after result is consumed.

### 3. Worker (`worker/`)

- **Process/Thread**: Runs in a loop, sleeping when the queue is empty, waking periodically.
- **Behavior**Behavior**:
  1. Check `task_queue` for a message (block with timeout or non‑block with sleep).
  2. If empty → sleep for a configurable interval (e.g., 1 second).
  3. If message found:
     - Pop message from queue.
     - Lookup task in Registry by `message["task"]`.
     - Change task state to `WAITING` (worker about to process).
     - Execute the task: `task_instance(*args, **message["kwargs"])`.
     - While executing, change state to `PROCESSING`.
     - After execution, store the result in the **Backend** using `Backend.put(task_id, result)`.
     - Update Registry: set state to `READY` and store the result (or a reference to the backend).
     - Optionally, hold the result in memory for a short cache lifetime.
  4. Repeat.

### 4. Backend / Database (`backend/`)

- **Custom Database interface**:
  - `put(task_id, result)` → append result to CSV file.
  - `get(task_id)` → retrieve result from CSV (scan or index).
  - `delete(task_id)` → remove result entry from CSV (or mark as deleted).

- **Implementation**:
  - Uses a plain‑text CSV file (e.g., `results.csv`) with columns:
    - `task_id`, `task_name`, `result`, `status`, `timestamp`
  - On each `put`, a new row is appended.
  - On `get`, the file is scanned (or an in‑memory index is maintained) to find the latest matching row.
  - `delete` can either remove the row (rewrite file) or mark `status` as `"DELETED"`.

- **Regular maintenance**:
  - The backend may periodically compact the CSV file to remove stale entries (optional, future improvement).

## Data Flow (End‑to‑End)

1. **Producer** calls `producer.dispatch(add, 2, 3)`.
2. Producer checks Registry for existing `add` task:
   - Not found → create, register as `PENDING`.
   - Enqueue message on `task_queue`.
3. **Worker** (on its next cycle) dequeues message.
4. Worker looks up task in Registry, sets state to `WAITING`.
5. Worker executes `add(2, 3)` → result = 5.
6. Worker calls `Backend.put(task_id, 5)`.
7. Worker updates Registry: state → `PROCESSING` → `READY`, stores result reference.
8. **Producer** (polling or event‑driven) detects `READY` state for `task_id`.
9. Producer calls `Backend.get(task_id)` to retrieve result.
10. Producer returns result to caller.
11. Optionally, Producer removes task from Registry (or keeps for cache).

## Querying & Caching

- **Producer caching**: If a task with the same name is already `READY`, subsequent `dispatch()` returns the result directly from Backend without re‑dispatching.
- **Grace period**: A `READY` task may be retained in Registry for a configurable TTL before removal, allowing multiple `dispatch` calls for the same function to get the cached result.

## CSV Result File Format

- **Location**: `celery_prac/results.csv` (configurable).
- **Columns**:

```csv
task_id,task_name,result,status,timestamp
550e8400-e29b-41d4-a716-446655440000,__main__.add,5,completed,2025-03-21T10:30:00
```

- **Access pattern**:
  - Append only for writes.
  - For `get`, read entire file (or maintain an in‑memory mapping keyed by `task_id` for fast lookup).
  - For `delete`, either rewrite file without the row or update status.

## Concurrency & Thread Safety

- The `queue.Queue` from Python standard library is thread‑safe.
- The Registry (`TaskRegistry`) will need locking if accessed from multiple threads (Producer and Worker run separately, but may share same process).
- Backend CSV writes should be serialised to avoid corruption (use file locking or append with `open` in append mode within a lock).

## Future Evolution (Post‑Spec)

1. Replace in‑memory queue with Redis/RabbitMQ.
2. Support multiple workers consuming from same queue.
3. Add proper error handling (retry, fail states).
4. Add real asynchronous polling (e.g., callbacks or event streams).
5. Persist Registry state across restarts.
6. Add CLI to inspect tasks and results.

---

*This document serves as the design blueprint for the `celery_prac` project. All implementation should follow these specifications.*
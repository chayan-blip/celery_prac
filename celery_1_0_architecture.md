# Celery 1.0 Architecture & Design

## Overview

Celery 1.0 is a distributed task queue implemented in Python. It uses a **message broker** (RabbitMQ via AMQP) to dispatch tasks from producers to **worker processes** which execute tasks asynchronously. Results are stored in a configurable **result backend**.

The architecture is modular with clear separation of concerns:

- **Task Definition & Registration** (`task/`, `registry.py`, `decorators.py`)
- **Message Publishing & Consumption** (`messaging.py`)
- **Task Execution** (`execute/`, `execute/trace.py`)
- **Worker Server** (`worker/`)
- **Result Backends** (`backends/`)
- **Configuration** (`conf.py`)
- **Utilities & Signals** (`utils.py`, `signals.py`)
- **Beat Scheduler** (`beat.py`)
- **Management Commands** (`management/`)

---

## 1. Task Definition & Registration

### 1.1 Task Class (`celery/task/base.py`)

- `Task` is the core class, inheriting from `object`. It uses the metaclass `TaskType`.
- The metaclass automatically registers a non-abstract Task subclass into the global registry `tasks` (a `TaskRegistry` instance).
- Key attributes: `name`, `abstract`, `type` (`"regular"` or `"periodic"`), `exchange`, `routing_key`, `max_retries`, `default_retry_delay`, `rate_limit`, `serializer`, `ignore_result`, `backend`.
- `__call__` delegates to `run()`.
- Class methods `delay()` → shortcut to `apply_async()` with star args; `apply_async()` → enqueues via the broker; `apply()` → executes locally (eager mode); `retry()` → re-queues the task with increased retry count.
- Lifecycle hooks: `on_success`, `on_failure`, `on_retry`.

### 1.2 TaskType Metaclass

- Intercepts class creation. If the class is not abstract and has `autoregister=True`, it automatically generates the task name as `"module.ClassName"` and calls `tasks.register(task_cls)`.
- Returns the already-registered class if it exists, ensuring singleton-like behaviour.

### 1.3 PeriodicTask

- Subclasses `Task` with `type = "periodic"` and `ignore_result = True`.
- Requires `run_every` attribute (a `timedelta` or integer seconds).
- Provides `is_due()` and `remaining_estimate()` for scheduling decisions.

### 1.4 Task Decorator (`celery/decorators.py`)

- `@task(**options)` decorator wraps any callable into a Task subclass.
- Internally creates a `run` method that calls the original function.
- Preserves the original function's argspec to enable default keyword argument injection.
- Supports `base`, `exchange`, etc. as keyword arguments.
- `@periodic_task()` is a wrapper that sets `base=PeriodicTask`.

### 1.5 TaskRegistry (`celery/registry.py`)

- Inherits from `UserDict`.
- Singletons `tasks` holds all registered tasks.
- `register(task)`: if the argument is a class, instantiates it; adds to `data` keyed by `task.name`.
- `unregister(name)`: removes a task, raising `NotRegistered` if not found.
- `regular()` / `periodic()`: filter tasks by type.

---

## 2. Message Layer (`messaging.py`)

- Based on **carrot** library (an AMQP abstraction).
- `TaskPublisher`: publishes task messages to the broker. Contains `delay_task()` which constructs a message dict (`task`, `id`, `args`, `kwargs`, `retries`, `eta`, optional `taskset`) and sends it via `self.send()`.
- `TaskConsumer`: consumes task messages from a specific queue.
- `EventPublisher` / `EventConsumer`: for monitoring events (task started, succeeded, failed).
- `BroadcastPublisher` / `BroadcastConsumer`: for remote control commands (e.g., revoke, rate limit).
- `establish_connection()`: creates a `DjangoBrokerConnection`.
- `with_connection` decorator: auto-connects and closes connection around a function.

---

## 3. Task Execution (`execute/`)

### 3.1 `celery/execute/__init__.py`

- `apply_async()`: main entry point for sending a task to a broker.
  - If `ALWAYS_EAGER` is set, falls back to local `apply()`.
  - Otherwise, uses `TaskPublisher.delay_task()` to send the message, then returns an `AsyncResult`.
- `apply()`: executes the task locally (synchronously). Uses `TaskTrace` and returns an `EagerResult`.
- `delay_task()`: shorthand for `apply_async(tasks[task_name], ...)`.

### 3.2 Trace (`execute/trace.py`)

- `TraceInfo`: captures execution outcome (status, retval, exception info).
- `TaskTrace`: wraps a task call with pre/post signals and dispatches to handlers based on result state (SUCCESS, RETRY, FAILURE).
  - Calls `task.on_success`, `task.on_retry`, or `task.on_failure`.
- Signals: `task_prerun`, `task_postrun` are emitted.

---

## 4. Worker Server (`worker/`)

The worker is a multi-threaded/multi-process system that listens to queues and executes tasks.

### 4.1 WorkController (`worker/__init__.py`)

- Main orchestrator. Components (in order of startup, and reverse shutdown):
  1. **TaskPool**: a multiprocessing pool of worker processes.
  2. **Mediator**: background thread that pulls tasks from the ready queue and dispatches them via `pool.apply_async()`.
  3. **ScheduleController**: thread managing ETA (time-based) scheduling – moves tasks due from the scheduler to the ready queue.
  4. **EmbeddedClockService**: optional beat scheduler thread (for periodic tasks).
  5. **CarrotListener**: main message consumer (uses a `ConsumerSet`) that receives AMQP messages and enqueues them into the ready queue (or eta schedule).

### 4.2 TaskPool (`worker/pool.py`)

- Wraps `multiprocessing.Pool` with a `TaskPool` that has `apply_async()` and `start()`, `stop()`.

### 4.3 Mediator (`worker/controllers.py`)

- Background thread that continuously calls `ready_queue.get(timeout=1)`.
- When a task wrapper is retrieved, it checks if the task has been revoked; if not, calls `self.callback(task)` which is `WorkController.process_task`.
- `process_task()` calls `wrapper.task.execute(wrapper, pool, ...)`.

### 4.4 ScheduleController (`worker/controllers.py`)

- Background thread iterating over an `eta_schedule` (a `Scheduler` instance).
- The `Scheduler` yields the delay until the next ETA task is due.
- The thread sleeps for that delay, then wakes up – the scheduler moves due tasks to the ready queue.

### 4.5 CarrotListener (`worker/listener.py`)

- Uses a `ConsumerSet` to consume from all configured queues.
- For each message, it calls `from_message()` on `TaskWrapper` and then decides whether to put it into the ready queue (immediate) or the ETA schedule (if `eta` is set).

### 4.6 Job/TaskWrapper (`worker/job.py`)

- `TaskWrapper`: encapsulates a single task message with `task_name`, `task_id`, `args`, `kwargs`, `retries`, `on_ack` callback.
- `from_message()`: factory method that parses the raw message dict.
- `execute()`: runs the task directly (in the main thread) using `WorkerTaskTrace.execute()`.
- `execute_using_pool()`: submits to the multiprocessing pool via `pool.apply_async(execute_and_trace, ...)`.
- `WorkerTaskTrace`: subclass of `TaskTrace` that also stores results in the backend (on success, failure, or retry) and handles email notifications on failure.

---

## 5. Result Backends (`backends/`)

- `default_backend` is obtained from `celery.backends`.
- Supports multiple backends: database, cache, AMQP, etc.
- `prepare_exception()`, `mark_as_done()`, `mark_as_retry()`, `mark_as_failure()` are the core methods.
- `BaseAsyncResult` is used to query task status/results later.

---

## 6. Periodic Task Scheduling (`beat.py`)

- `BeatService` / `EmbeddedClockService` runs a thread that periodically checks the celerybeat schedule file for due periodic tasks.
- For each due task, it publishes a task message via `TaskPublisher.delay_task()`.

---

## 7. Configuration (`conf.py`)

- Settings loaded from Django settings (or a settings module).
- Defaults provided for all options: `CELERY_ALWAYS_EAGER`, `CELERY_BACKEND`, `CELERY_DEFAULT_ROUTING_KEY`, `CELERYD_CONCURRENCY`, etc.
- Routing table built from `CELERY_QUEUES` dict (or deprecated legacy settings).
- Module-level variables accessed throughout the code (e.g., `conf.ALWAYS_EAGER`).

---

## 8. Key Flows

### 8.1 Async Task Dispatch

```
User code: @task() def mytask(...); mytask.delay(args)
  → Task.delay(args) → Task.apply_async(args, kwargs)
    → celery.execute.apply_async()
        → if ALWAYS_EAGER: return apply()  (synchronous)
        → else: _apply_async()
          → get task instance from registry
          → establish AMQP connection
          → TaskPublisher.delay_task(task_name, args, kwargs, eta, ...)
            → build message dict, send to exchange
            → return AsyncResult(task_id)
```

### 8.2 Worker Processing

```
AMQP message arrives
  → CarrotListener receives message
    → TaskWrapper.from_message(message, data)
      → if eta present: put into ETA schedule
      → else: put into ready_queue (TaskBucket or simple Queue)
  → Mediator thread: get task from ready_queue
    → check not revoked
    → WorkController.process_task(wrapper)
      → wrapper.task.execute(wrapper, pool, loglevel, logfile)
        → wrapper.execute_using_pool(pool, ...)
          → wrapper._set_executed_bit() + ack the message
          → pool.apply_async(execute_and_trace, args=(task_name, task_id, args, kwargs))
  → Worker process: execute_and_trace()
    → WorkerTaskTrace(task_name, task_id, args, kwargs)
      → extends kwargs with standard keyword args (logfile, loglevel, task_id, task_retries, task_name)
      → TraceInfo.trace(task.fun, args, kwargs)
        → calls task.run(*args, **kwargs)
        → captures SUCCESS / RETRY / FAILURE
      → based on outcome:
        → handle_success: mark_as_done in backend, call on_success
        → handle_retry: mark_as_retry, call on_retry, return ExceptionInfo
        → handle_failure: mark_as_failure, call on_failure, return ExceptionInfo
```

### 8.3 Retry Flow

```
Task raises RetryTaskError (or calls self.retry())
  → apply_async is called again with retries incremented
  → Broker re-dispatches the message
  → Worker processes again; on retry > max_retries → raises MaxRetriesExceededError
```

### 8.4 Periodic Task Flow

```
Beat scheduler (celerybeat or embedded clock)
  → Every loop interval, checks all periodic tasks' `is_due(last_run_at)`
  → For tasks that are due:
    → publish task message (like an async dispatch)
    → update last_run_at in schedule file
```

---

## 9. Design Patterns & Highlights

- **Metaclass-based auto-registration**: `TaskType` automatically registers tasks, avoiding boilerplate.
- **Singleton registry**: global `tasks` dict ensures task classes are unique.
- **Strategy pattern**: result backends are pluggable.
- **Decorator-to-class**: the `@task` decorator dynamically creates a Task subclass using `type()` and registers it.
- **Thread + Process model**: Worker uses background threads (Mediator, Scheduler, Listener) feeding a multiprocessing pool for concurrent execution.
- **Signals**: For extension points (task_prerun, task_postrun, task_sent, worker_shutdown).
- **Message protocol**: Simple JSON-like dict with `task`, `id`, `args`, `kwargs`, `retries`, `eta`, `taskset`.
- **Eager mode**: For development/testing, tasks can be executed synchronously without a broker.

---

## 10. Notable Observations & Potential Improvements (from analysis of `celery_prac` demo project)

The custom implementation in `celery_prac` mimics only the registration and decorator part:
- `dec` decorator creates a Task subclass and registers it with a `TaskRegistry`.
- Missing: worker, messaging, result backends, async dispatch, retry logic, periodic tasks, full lifecycle hooks.

**Improvements for the demo project**:

1. **Add `wraps` decorator** to preserve the original function's metadata in `dec`.
2. **Support decorator arguments** like `@dec(name='my_task', base=MyBaseTask)`.
3. **Implement async dispatch** via a message broker (even a simple in-memory queue for demonstration).
4. **Add execution layer** (eager/async) with result tracking.
5. **Add lifecycle hooks** (on_success, on_failure, on_retry).
6. **Support periodic tasks** with a scheduler.
7. **Add error handling and retry logic** similar to Celery's `MaxRetriesExceededError` / `RetryTaskError`.
8. **Add proper test coverage** for the decorator and registry.

---

*This document captures the architecture of Celery 1.0 based on a thorough reading of the source code. It is intended for reference and further development analysis.*
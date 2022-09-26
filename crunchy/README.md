# disq
A task queue for distributed processing....For practice copying code from celery/crunchy

===================
celery - Distributed Task Queue for Django
===================

Authors:
    Ask Solem (askh@opera.com)
Version: 0.1.8

Introduction
-----------------------------------------------------------------------------------------

`` celery ``is a distributed tasks queue framework for Django
More information will follow
You can install celery either via Python Package Index (PyPI)
or from source

To install ``pip``,::
    
    $ pip install celery

To install using ``easy_install``

    $easy_install celery

If you have downloaded a source tarball, you can install it by doing the following
    python setup.py build 
    python setup.py install # as root

Usage
=============

Have to write a cool tutorial, but here is some simple usage info
*Note* You need to have a AMQP message broker running, like `RabbitMQ _`,
and you need to have the ampq server setup in your settings file, as described
in the `carrot distribution README` _

*Note* If you're running ``SQLite`` as the database backend ``celeryd`` will 
only be able to process one message at a time, this is because ``SQLite`` doesn't 
allow concurrent writes

.._`RabbitMQ`: http://www.rabbitmq.com
.._`carrot distribution README`: http://pypi.python.org/pypi/carrot/0.3.3

Defining tasks
-------------------
    >>>> from celery.task import tasks
    >>>> from celery.log import setup_logger
    >>>> def do_something(some_arg, **kwargs):
    ...       logger = setup_logger(**kwargs)
    ...       logger.info("Did something: %s" some_arg)
    >>>> task.register(do_something, "do_something")

*Note* Task functions only supports keyword arguments 
Tell the celery daemon to run a task
---------------------------------------------
    >>>> from celery.task import delay_task
    >>>> delay_task("do_something", some_arg="foo bar baz")

Running the celery daemon
--------------------------------

:: 
    $ cd mydjangoproject
    $ env DJANGO_SETTINGS_MODULE=settings celeryd
    [........]
    [2009-04-23 17:44:05,115: INFO/Process-1] Did something: foo bar baz
    [2009-04-23 17:44:05,118: INFO/MainProcess] Waiting for queue.

Auto discovery of tasks
------------------------------

```celery``` has an autodiscovery feature like the Django Admin, that 
automatically loads any ``tasks.py`` module in the applications listed in
``settings.INSTALLED_APPS``

A good place to add this command could be in your ``urls.py``

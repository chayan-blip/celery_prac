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

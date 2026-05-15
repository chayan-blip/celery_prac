from celery_prac.decorator import task

@task
def add (a, b):
    return a + b


from celery_prac.decorator import dec


@dec
def add (a, b):
    return a + b


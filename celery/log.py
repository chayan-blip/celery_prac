import multiprocessing
import os
import time
import logging
from celery.conf import LOG_FORMAT, DAEMON_LOG_LEVEL

def setup_logger(loglevel=DAEMON_LOG_LEVEL, logfile=None, format=LOG_FORMAT, **kwargs):
    """"Setup the ``multiprocessing`` logger. If ``logfile`` is not specified,
    ``stderr`` is used.
    Returns the logger object.
    """
    logger = multiprocessing.get_logger() ## create a logger object using multiprocessing lib
    if logfile: ## if the log file already exists then create a log handler in order to log all events
        if hasattr(logfile, "write"):
            log_file_handler = logging.StreamHandler(logfile)
        else:
            log_file_handler = logging.FileHandler(logfile)
        formatter = logging.Formatter(format) ## take the log format obtained from django settings
        ## and use it to specify the format in which the log file will be printed
        ## here we are using time, process number, what type of message (warning/error etc) and message itself
        log_file_handler.setFormatter(formatter) ## pass the formatter object to the log file handler
        logger.addHandler(log_file_handler) ## pass the log file handler to the logger object for logging
    else:
        multiprocessing.log_to_stderr() ## if the log file does not exists then output the error
        ## into system error stream for display in terminal
    logger.setLevel(loglevel) ## set the events which will be logged, for eg all Warnings + error / only all errors etc
    return logger ## pass the logger object

def emergency_error(logfile, message):
    """Emergency error logging, for when there's no standard file
    descriptors open because the process has been daemonized or for
    some other reason"""
    logfh_needs_to_close = False
    if hasattr(logfile, "write"):
        logfh = logfile
    else:
        logfh = open(logfile, "a")
        logfh_needs_to_close = True
    logfh.write("[%(asctime)s : FATAL/%(pid)d]: %(message)s \n" % {
        "asctime" : time.asctime(), ## note the present time , convert to string and write to message
        "pid":os.getpid(), ## get the other details like pid, and message , and write them
        ## basically simulating the task done by the logger using a file handler
        "message":message
    })
    if logfh_needs_to_close:
        logfh.close() ## safely close the file
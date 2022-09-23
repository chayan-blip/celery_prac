import imp
from django.conf import settings
from django.core import exceptions

def autodiscover():
    """Include tasks for all applications in settings.INSTALLED_APPS"""
    return filter(None, [tasks_for_app(app) for app in settings.INSTALLED_APPS])
    ## find the installed apps in the settings and return an iterator invoking tasks for app

def tasks_for_app(app):
    """Given an application name, imports any tasks.py file for that app"""
    def found_tasks_module_handler(app_path, app_basename):
        return __import__("%s.tasks" %app)
    return find_related_module(app,"tasks", found_tasks_module_handler) ## return the handler asssociated 
    ## with the tasks found for that given app

def find_related_module(app, related_name, handler):
    """Given an application name and a module name, tries to find that 
    module in the application, and running handler if it finds it"""
    # admin.py is executed whenever django loads URLconf from urls.py in order to read the app configuration 
    # from the specified url. The autodiscover() will search for all the apps in the INSTALLED_APPS
    # one by one and executes the code present in that file
    # See django.contrib.admin.autodiscover for an explanation of this code
    try:
        app_basename = app.split('.')[-1] ## find the module name
        app_path = __import__(app, {}, {}, app_basename).__path__ ## find the module path
    except AttributeError:
        return None

    try:
        imp.find_module(related_name,app_path) ## find the path in order to import the module for execution
    except ImportError:
        return None
    
    return handler(app_path, app_basename) ## return a handler to the function being imported with the 
    ## given app name and path

    ########################################################################################
    # present understanding with respect to functionality is that django daemon runs in the background
    # and accesses the handlers of each of the tasks mentioned in the settings. An handler may be a daemon like 
    # object running the task in the os user space in the background
    # this may be done in  order to not start a new task but rather accumulating the running functions and
    # giving them new tasks to perform instead of killing and restarting them , or just to start a new process
    # from the same app which is busy with another running process of the same task
    ########################################################################################
## Things kick off from crunch d
## First take the arguments from parser
## parse them and store them in an object to be passed to the main
    ## main runs taking concurrency, logger parameters, queue and pid parameters
    ## parsed from django settings files
    ## all these variables are parsed and collected to dictionaries, lists etc
    ## which the main starts with by importing
    ## check for the database engine, if sqlite check whether the concurrency is 1 else
    ## throw warning and start with 1
    ## TODO add with daemon flow
    ## if the daemon is not initially running then invoke the autodiscover
    ## function
    ## the auto discover will create a list of apps from settings.APPS where
    ## if the module is found then it will import app.task file
    # Now initialize the crunchy daemon
    # initializing the crunchy daemon will setup the logger
    # create a process pool containing threads 
    # create a consumer and initialize the task registry
    # now crunchd run will be invoked 
    # This will initialize a process q
    # The run process will keep running 
    # run will try to fetch the next message from the process
    #  q 

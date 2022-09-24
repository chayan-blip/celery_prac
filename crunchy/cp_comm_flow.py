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
    ## this autodiscover function will go the django settings file in django
    ## library and then run an iterator

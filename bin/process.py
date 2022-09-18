from UserList import UserList

class ProcessQueue(UserList):
    """Queue of running child processes, which starts waiting for the
    processes to finish """

    def __init__(self, limit, logger=None, done_msg=None):
        self.limit = limit    ## set the data limit, initialize the logger and set the 
        self.logger = logger  ## the message to be sent back on being successful
        self.done_msg = done_msg ## back to the producer ??
        self.data = []        ## log all the data associated with the task
    
    def add(self, result, task_name, task_id):
        self.data.append([result, task_name, task_id]) ## record the list with 
        ## task details

        if self.data and len(self.data) >= self.limit: ## Each data 
            ## Element in the user defined list has a maximum
            ## size limit, In case the arguments are more than
            ## that, then log the details using loggger into the log file
            for result, task_name, task_id in self.data:
                ret_value = result.get() ## get the result 
                ## method not implemented
                if self.done_msg and self.logger: ## If the task
                    ## is completed log it
                    self.logger.info(self.done_msg % {
                        "name": task_name,   ## Same format as add data
                        "id": task_id,
                        "return_value": ret_value})
            self.data = [] ## append an empty list

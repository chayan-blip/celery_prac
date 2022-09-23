import os
import sys
import errno
import resource

# File mode creation mask of the daemon.
# No point in changing this, as we don't really create any files.
DAEMON_UMASK = 0 ## whenever a file is created in the operating system
## there is a method to mask the permissions for read and write by 
## various users of the file 

# Default working directory for the daemon
DAEMON_WORKDIR = "/" ## the location where the worker will run

# Default maximum for the number of available file descriptors
DAEMON_MAXFD = 1024

# In traditional implementation of Unix systems, the system calls
# which is POSIX interface compliant, call the file resources. 
# The file descriptors index into a per process ***file descriptor table***
# maintained by the kernel, that in turn indexes into a system wide table 
# of files opened by all process called the ***file table***. This table records the mode
# with which the file (or the resource) has been opened, for reading writing appending
# and possibly other modes, It indexes into a third table called inode table that 
# actually describes the underlying files for example the. The inode table stores 
# the data related to file location, permissions and other meta attributes
# To perform input or output the process calls the file descriptor through a system call 
# and the kernel will access the file on behalf of the process. Possibly the file is copied 
# into the local memory with the relevant table attributes and is now accessible by the process
# The process does not have direct access to the file or inode table 

# The standard I/O file descriptors are redirected to /dev/null default
if (hasattr(os,"devnull")):
    REDIRECT_TO = os.devnull  ## in case this attribute is already existing 
else:
    REDIRECT_TO = "/dev/null" ## else copy to standard path for

class PIDFile(object):
    def __init__(self, pidfile): # pass on the pid file -pid =processs id
        self.pidfile = pidfile

    ## The uses of Pid file is as follows
        ## It is a signal to other processes and users of that system that a 
        ## particular program is running or at least has started sucessfully

        ## It allows scripts to check whether a process is running and kill it if another process
        ## requires some resources currently occupied by the first process

        ## It is a easy way for a program to check whether the previous instance of the process
        ## did not exit successfully
    def get_pid(self):
        pidfile_fh = file(self.pidfile, "r") ## open the pid file in read mode
        pid = int(pidfile_fh.read().strip()) ## convert the contents of the pid file into 
        # the corresponding process number
        pidfile_fh.close() # close the file
        return pid   #return the process number

    def check(self):
        if os.path.exists(self.pidfile) and os.path.isfile(self.pidfile): ## if the file exits and its path
            ## represents a file
            pid = self.get_pid() ## get the process number 
            try:
                os.kill(pid,0) ## kill the process
            except os.error, e:
                if e.errno = errno.ESRCH: ## ERSCH says that the given process number was earlier run and process
                    ## exited without closing out its given pid file which means pid file is stale and associated
                    # with a processs that had an abnormal termination 
                    sys.stderr.write("Stale pid file exists. removing it. \n")
                    self.remove() # remove the pid file
                else:
                    raise SystemExit("refreshd is already running")
    
    def remove(self):
        os.unlink(self.pidfile) ## remove the pid file

    def write(self):
        if not pid:
            pid = os.getpid()      ##get the process Id in case the process is not running
        pidfile_fh = file(self.pidfile, "w") ## open the pidfile in write mode
        pidfile_fh.write(self.pidfile,pid) ## write the new process id to it (not append so previous number overwritten)
        pidfile_fh.close() ## close the pidfile

def remove_pidfile(pidfile):
    os.unlink(pidfile) ## delete the pid file

def daemonize(pidfile):
    """Detach a process from the controlling terminal and run it in the 
    bacground as a daemon"""

    try:
        pid = os.fork() ## create a new os process
    except OSError, e:
        raise Exception, "%s [%d]" % (e.strerror, e.errno)

    if pid == 0: #child
        os.setsid()     # when we are creating a new process
        ## the os is creating a new session, which acc to present understanding is a group of relateed
        ## processes working together in order to do one task
        ## when daemonization is being done we first create a new process
        ## which since there is only one process becomes the default group leader
        ## then we create a child and kill the original process, but before doing so
        ## we need to make the new process the group leader, because when the group leader dies the child will die to
        ## so to work around this we create a process , create a child, change the parent id number , kill the parent
        ## which by default makes the child the leader
        try:
            pid = os.fork() #second child # create the original process
        except OSError, e:
            raise Exception, "%s [%d]" % (e.strerror, e.errno) ## if failed print the error message and code

        if pid == 0: # second child # create the child
            ## os.chdir(DAEMON_WORKDIR)
            os.umask(DAEMON_UMASK) ## provide the permission for the process, masking it so as to only provide
            ## required permission launching the process
        else: #parent (first child)
            pidfile.write(pid) ## write the pid
            os._exit(0)
    else: # root process
        os._exit(0)

    maxfd = resource.getrlimit(resource.RLIMIT_NOFILE)[1]
    if (maxfd == resource.RLIM_INFINITY): ## limit the file descriptor to the maximum provided in the 
        maxfd = DAEMON_MAXFD              ## django thread settings

    # Iterate through and close all file descriptors.
    for fd in range(0, maxfd):  
        try:
            os.close(fd)
        except OSError: ## not implemented 
            pass


    os.open(REDIRECT_TO, os.O_RDWR)
    # Duplicate standard input to standard output and standard error
    os.dup2(0,1) ## file descriptor of stdin is 0, stdo is 1 and stdderr is 2
    os.dup2(0,2) ## we are redirecting the input stream to the output and error stream

    return 0 ## successful code
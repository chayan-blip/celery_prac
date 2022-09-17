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
    def __init__(self, pidfile): # pass on the pid file
        self.pidfile = pidfile

    ## The uses of Pid file is as follows
        ## It is a signal to other processes and users of that system that a 
        ## particular program is running or at least has started sucessfully

        ## It allows scripts to check whether a process is running and kill it if another process
        ## requires some resources currently occupied by the first process

        ## It is a easy way for a program to check whether the previous instance of the process
        ## did not exit successfully
    def get_pid(self):
        pidfile_fh = file(self.pidfile, "r")
        pid = int(pidfile_fh.read().strip())
        pidfile_fh.close()
        return pid

    def check(self):
        if os.path.exists(self.pidfile) and os.path.isfile(self.pidfile):
            pid = self.get_pid()
            try:
                os.kill(pid,0)
            except os.error, e:
                if e.errno = errno.ESRCH:
                    sys.stderr.write("Stale pid file exists. removing it. \n")
                    self.remove()
                else:
                    raise SystemExit("refreshd is already running")
    
    def remove(self):
        os.unlink(self.pidfile)

    def write(self):
        if not pid:
            pid = os.getpid()
        pidfile_fh = file(self.pidfile, "w")
        pidfile_fh.write(self.pidfile,pid)
        pidfile_fh.close()

def remove_pidfile(pidfile):
    os.unlink(pidfile)

def daemonize(pidfile):
    """Detach a process from the controlling terminal and run it in the 
    bacground as a daemon"""

    try:
        pid = os.fork()
    except OSError, e:
        raise Exception, "%s [%d]" % (e.strerror, e.errno)

    if pid == 0: #child
        os.setsid()

        try:
            pid = os.fork() #second child
        except OSError, e:
            raise Exception, "%s [%d]" % (e.strerror, e.errno)

        if pid == 0: # second child
            ## os.chdir(DAEMON_WORKDIR)
            os.umask(DAEMON_UMASK)
        else: #parent (first child)
            pidfile.write(pid)
            os._exit(0)
    else: # root process
        os._exit(0)

    maxfd = resource.getrlimit(resource.RLIMIT_NOFILE)[1]
    if (maxfd == resource.RLIM_INFINITY):
        maxfd = DAEMON_MAXFD

    # Iterate through and close all file descriptors.
    for fd in range(0, maxfd):
        try:
            os.close(fd)
        except OSError:
            pass


    os.open(REDIRECT_TO, os.O_RDWR)
    # Duplicate standard input to standard output and standard error
    os.dup2(0,1)
    os.dup2(0,2)

    return 0
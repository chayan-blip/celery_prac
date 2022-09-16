import os
import sys
import errno
import resource

# File mode creation mask of the daemon.
# No point in changing this, as we don't really create any files.
DAEMON_UMASK = 0

# Default working directory for the daemon
DAEMON_WORKDIR = "/"

# Default maximum for the number of available file descriptors
DAEMON_MAXFD = 1024

# The standard I/O file descriptors are redirected to /dev/null default
if (hasattr(os,"devnull")):
    REDIRECT_TO = os.devnull
else:
    REDIRECT_TO = "/dev/null"

class PIDFile(object):
    def __init__(self, pidfile):
        self.pidfile = pidfile

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
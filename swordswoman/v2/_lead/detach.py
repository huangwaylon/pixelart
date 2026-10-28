# Double-fork + setsid so the child is reparented to launchd and survives the lead session.
import os, sys
if os.fork(): sys.exit(0)
os.setsid()
if os.fork(): sys.exit(0)
fd = os.open(os.devnull, os.O_RDWR); [os.dup2(fd, i) for i in (0, 1, 2)]
os.execvp(sys.argv[1], sys.argv[1:])

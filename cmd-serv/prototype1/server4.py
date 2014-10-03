import zmq
import time
import sys
import os
import pwd
import grp

ipc_sock = "/run/cmdsrv_sock"

owner = pwd.getpwnam("apache")
group = grp.getgrnam("xsce-admin")

context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind("ipc://%s" % ipc_sock )

os.chown(ipc_sock, owner.pw_uid, group.gr_gid)
os.chmod(ipc_sock, 0770)

while True:
    #  Wait for next request from client
    message = socket.recv()
    print "Received request: ", message
    time.sleep (1)
    socket.send("World from %s" % ipc_sock)

import zmq
import time
import sys
import os
import pwd
import grp

ipc_sock = "/tmp/cmdsrv_sock"

root_user = pwd.getpwnam("root")
admin_grp = grp.getgrnam("xsce-admin")

context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind("ipc://%s" % ipc_sock )

os.chown(ipc_sock, root_user.pw_uid, admin_grp.gr_gid)
os.chmod(ipc_sock, 0660)

while True:
    #  Wait for next request from client
    message = socket.recv()
    print "Received request: ", message
    time.sleep (1)
    socket.send("World from %s" % ipc_sock)

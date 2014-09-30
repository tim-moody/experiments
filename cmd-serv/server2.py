import zmq
import time
import sys

ipc_sock = "socks/mysock"

context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind("ipc://%s" % ipc_sock )

while True:
    #  Wait for next request from client
    message = socket.recv()
    print "Received request: ", message
    time.sleep (1)
    socket.send("World from %s" % ipc_sock)

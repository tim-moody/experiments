import zmq
import sys

ipc_sock = "/run/cmdsrv_sock"

context = zmq.Context()
print "Connecting to server..."
socket = context.socket(zmq.REQ)
socket.connect ("ipc://%s" % ipc_sock)

#  Do 5 requests, waiting each time for a response
for request in range (1,5):
    print "Sending request ", request,"..."
    socket.send ("Hello")
    #  Get the reply.
    message = socket.recv()
    print "Received reply ", request, "[", message, "]"

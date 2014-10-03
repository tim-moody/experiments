import zmq
import sys

if  len(sys.argv) != 2:
  print 'usage: cmdsrv-ctl "<message>"'
  sys.exit(0)

send_msg = sys.argv[1]
print "message to send: ", send_msg

ipc_sock = "/run/cmdsrv_sock"

context = zmq.Context()
print "Connecting to server..."
socket = context.socket(zmq.REQ)
socket.connect ("ipc://%s" % ipc_sock)

socket.send (send_msg)

#  Get the reply.

reply_msg = socket.recv()
print "Received reply: ", reply_msg

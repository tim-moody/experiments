import zmq
import sys

def application(environ, start_response):
  ipc_sock = "/run/cmdsrv_sock"

  message="dummy message"

  status = '200 OK'
  response_headers = [('Content-type', 'text/html')]
  start_response(status, response_headers)

  context = zmq.Context()
  socket = context.socket(zmq.REQ)
  socket.connect ("ipc://%s" % ipc_sock)

  socket.send ("Hello")
  #  Get the reply.
  message = socket.recv()

  page = "<html> <body> <h1>Hello world!</h1> <p>This is being served using mod_wsgi</p>message: %s </body></html>" % message

  return page

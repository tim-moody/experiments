"""

   XSCE Multi-threaded Polling Command server

   Author: Tim Moody <tim(at)timmoody(dot)com>
   Contribution: Guillaume Aubert (gaubert) <guillaume(dot)aubert(at)gmail(dot)com>
                 Felipe Cruz <felipecruz@loogica.net>

"""
    
import time
import threading
import zmq
import sys
import os
import pwd
import grp

def tprint(msg):
    """like print, but won't get newlines confused with multiple threads DELETE AFTER TESTING"""
    sys.stdout.write(msg + '\n')
    sys.stdout.flush()

def main():
    """Server routine"""

    url_worker_data = "inproc://worker_data"
    url_worker_control = "inproc://worker_control"
    ipc_sock = "/run/cmdsrv_sock"
    url_client = "ipc://" + ipc_sock
    
    owner = pwd.getpwnam("apache")
    group = grp.getgrnam("xsce-admin")

    # Prepare our context and sockets
    context = zmq.Context.instance()

    # Socket to talk to clients
    clients = context.socket(zmq.ROUTER)
    clients.bind(url_client)
    os.chown(ipc_sock, owner.pw_uid, group.gr_gid)
    os.chmod(ipc_sock, 0770)

    # Socket to talk to workers
    workers_data = context.socket(zmq.DEALER)
    workers_data.bind(url_worker_data)

    # Launch pool of worker threads
    for i in range(5):
        thread = threading.Thread(target=worker_routine, args=(url_worker_data,))
        thread.start()
        

    poll = zmq.Poller()
    poll.register(clients, zmq.POLLIN)
    poll.register(workers_data, zmq.POLLIN)

    while True:
        sockets = dict(poll.poll())
        if clients in sockets:
            ident, msg = clients.recv_multipart()
            tprint('sending message server received from client to worker %s id %s' % (msg, ident))
            workers_data.send_multipart([ident, msg])
        if workers_data in sockets:
            ident, msg = workers_data.recv_multipart()
            tprint('Sending worker message to client %s id %s' % (msg, ident))
            clients.send_multipart([ident, msg])

    # We never get here but clean up anyhow
    clients.close()
    workers.close()
    context.term()
    
def worker_routine(worker_data_url, context=None):
    """Worker routine"""
    context = context or zmq.Context.instance()
    # Socket to talk to dispatcher
    data_socket = context.socket(zmq.DEALER)

    data_socket.connect(worker_data_url)
    msg = "World"

    while True:

        #string  = data_socket.recv()
        ident, string = data_socket.recv_multipart()

        print("Received request: [ %s ]" % (string))

        # do some 'work'
        time.sleep(1)

        #send reply back to client
        #data_socket.send(b"World")
        data_socket.send_multipart([ident, msg])



# Now start the application
if __name__ == "__main__":
    main()    

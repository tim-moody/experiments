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

def main():
    """Server routine"""

    url_worker_data = "inproc://worker_data"
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
    workers = context.socket(zmq.DEALER)
    workers.bind(url_worker_data)

    # Launch pool of worker threads
    for i in range(5):
        thread = threading.Thread(target=worker_routine, args=(url_worker_data,))
        thread.start()

    zmq.device(zmq.QUEUE, clients, workers)

    # We never get here but clean up anyhow
    clients.close()
    workers.close()
    context.term()
    
def worker_routine(worker_data_url, context=None):
    """Worker routine"""
    context = context or zmq.Context.instance()
    # Socket to talk to dispatcher
    data_socket = context.socket(zmq.REP)

    data_socket.connect(worker_data_url)

    while True:

        string  = data_socket.recv()

        print("Received request: [ %s ]" % (string))

        # do some 'work'
        time.sleep(1)

        #send reply back to client
        data_socket.send(b"World")



# Now start the application
if __name__ == "__main__":
    main()    

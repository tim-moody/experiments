"""

   Multithreaded Hello World server

   Author: Guillaume Aubert (gaubert) <guillaume(dot)aubert(at)gmail(dot)com>

"""
    
import time
import threading
import zmq
import sys
import os
import pwd
import grp

def worker_routine(worker_url, context=None):
    """Worker routine"""
    context = context or zmq.Context.instance()
    # Socket to talk to dispatcher
    socket = context.socket(zmq.REP)

    socket.connect(worker_url)

    while True:

        string  = socket.recv()

        print("Received request: [ %s ]" % (string))

        # do some 'work'
        time.sleep(1)

        #send reply back to client
        socket.send(b"World")

def main():
    """Server routine"""

    url_worker = "inproc://workers"
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
    workers.bind(url_worker)

    # Launch pool of worker threads
    for i in range(5):
        thread = threading.Thread(target=worker_routine, args=(url_worker,))
        thread.start()

    zmq.device(zmq.QUEUE, clients, workers)

    # We never get here but clean up anyhow
    clients.close()
    workers.close()
    context.term()

if __name__ == "__main__":
    main()    

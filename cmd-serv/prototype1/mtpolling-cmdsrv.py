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
    workers_control = context.socket(zmq.PUB)
    workers_control.bind(url_worker_control)

    # Launch pool of worker threads
    for i in range(5):
        thread = threading.Thread(target=worker_routine, args=(url_worker_data,url_worker_control,))
        thread.start()
        

    poll = zmq.Poller()
    poll.register(clients, zmq.POLLIN)
    poll.register(workers_data, zmq.POLLIN)    

    while True:
        sockets = dict(poll.poll())
        if clients in sockets:
            ident, msg = clients.recv_multipart()
            tprint('sending message server received from client to worker %s id %s' % (msg, ident))
            if msg == "STOP":
                workers_control.send("EXIT")
            else:
               workers_data.send_multipart([ident, msg])
        if workers_data in sockets:
            ident, msg = workers_data.recv_multipart()
            tprint('Sending worker message to client %s id %s' % (msg, ident))
            clients.send_multipart([ident, msg])

    # We never get here but clean up anyhow
    clients.close()
    workers.close()
    context.term()
    
def worker_routine(worker_data_url, url_worker_control, context=None):
    """Worker routine"""
    context = context or zmq.Context.instance()
    # Socket to talk to dispatcher
    data_socket = context.socket(zmq.DEALER)
    data_socket.connect(worker_data_url)
    
    control_socket = context.socket(zmq.SUB)
    control_socket.connect(url_worker_control)
    
    cmd_msg = "World"
    
    poll = zmq.Poller()
    poll.register(data_socket, zmq.POLLIN)
    poll.register(control_socket, zmq.POLLIN)   

    while True:
    
        sockets = dict(poll.poll())
        # process command
        if data_socket in sockets:
            ident, cmd_msg = data_socket.recv_multipart()
            tprint('sending message server received from client to worker %s id %s' % (cmd_msg, ident))
            data_socket.send_multipart([ident, cmd_msg])
        if control_socket in sockets:
            ctl_msg = control_socket.recv()
            tprint('got ctl msg %s in worker %s' % (ctl_msg, ident))
#            clients.send_multipart([ident, msg])
# look for EXIT


# Now start the application
if __name__ == "__main__":
    main()    

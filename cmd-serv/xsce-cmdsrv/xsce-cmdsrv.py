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
import subprocess
import sqlite3
import json
import yaml
import re

# Global Variables
last_command_rowid = 0
last_job_rowid = 0

# vars read from ansible vars directory
# effective is composite where local takes precedence

default_vars = None
local_vars = None
effective_vars = None
xsce_ansible_path = "/root/xsce"
ansible_facts = None

# vars set by admin-console
config_vars = None

def tprint(msg):
    """like print, but won't get newlines confused with multiple threads DELETE AFTER TESTING"""
    sys.stdout.write(msg + '\n')
    sys.stdout.flush()

def main():
    """Server routine"""
    
    init()
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
    
    server_run = True

    while server_run == True:
        sockets = dict(poll.poll())
        if clients in sockets:
            ident, msg = clients.recv_multipart()
            tprint('sending message server received from client to worker %s id %s' % (msg, ident))
            if msg == "STOP":
                # Tell the worker threads to shut down
                tprint('sending control message server received from client to worker %s id %s' % (msg, ident))
                workers_control.send("EXIT")
                clients.send_multipart([ident, "OK"])
                time.sleep(3)
                server_run = False
            else:
                tprint('sending data message server received from client to worker %s id %s' % (msg, ident))
                workers_data.send_multipart([ident, msg])
        if workers_data in sockets:
            ident, msg = workers_data.recv_multipart()
            tprint('Sending worker message to client %s id %s' % (msg, ident))
            clients.send_multipart([ident, msg])

    # Clean up if server is stopped
    clients.close()
    workers_data.close()
    workers_control.close()
    context.term()
    sys.exit()
    
def worker_routine(worker_data_url, url_worker_control, context=None):
    """Worker routine"""
    context = context or zmq.Context.instance()
    # Socket to talk to dispatcher
    data_socket = context.socket(zmq.DEALER)
    data_socket.connect(worker_data_url)
    
    control_socket = context.socket(zmq.SUB)
    control_socket.connect(url_worker_control)
    control_socket.setsockopt(zmq.SUBSCRIBE,"")
    
    poll = zmq.Poller()
    poll.register(data_socket, zmq.POLLIN)
    poll.register(control_socket, zmq.POLLIN)   
    
    worker_run = True
    
    while worker_run == True:
    
        sockets = dict(poll.poll())
        # process command
        if data_socket in sockets:
            ident, cmd_msg = data_socket.recv_multipart()
            tprint('sending message server received from client to worker %s id %s' % (cmd_msg, ident))
            cmd_resp = cmd_handler(cmd_msg)
            data_socket.send_multipart([ident, cmd_resp])
        if control_socket in sockets:
            ctl_msg = control_socket.recv()
            tprint('got ctl msg %s in worker' % ctl_msg)
            if ctl_msg == "EXIT":
                # stop loop in order to terminate thread   
                worker_run = False
                
    # Clean up if thread is stopped
    data_socket.close()
    control_socket.close()
    #context.term()             
    #sys.exit()        

def cmd_handler(cmd):
    # check for malicious characters and return error if found
    bad_command = validate_command(cmd)
    if bad_command != None:
        return (bad_command)
        
    # store the command
    store_command(cmd)
    
    # process the command
    resp = cmd + " done."
    avail_cmds = {
                 "TEST": do_test,
                 "LIST": list_library,
                 "WGET": wget_file
                 }                         
    try:
        resp = avail_cmds[cmd](cmd)
    except KeyError:
        resp = '{"Error": "Unknown Command"}'        
    return (resp)

def do_test(cmd):
    resp = '{"test": "xxx"}'    
    return (resp)
    
def list_library(cmd):
    resp = subprocess.check_output(["scripts/list_libr.sh"])
    json_resp = json_array("library_list", resp)    
    #proc = subprocess.Popen(['python','fake_utility.py'],stdout=subprocess.PIPE)   
    return (json_resp)
    
def wget_file(cmd):
    resp = cmd + " done."
    
    return (resp)
        
def json_array(name, str):
    try:
        str_array = str.split('\n')
        str_json = json.dumps(str_array)
        json_resp = '{ "' + name + '":' + str_json + '}'
    except StandardError:
        json_resp = cmd_error()
    return (json_resp)
    
def validate_command(cmd):
    if re.search('[;,|<>()=&\r\n]', cmd, flags=0):
        return ('{"Error": "Malformed Command."}')
    else:
        return None

def cmd_error():
    return ('{"Error": "Internal Server Error processing Command."}')   
    
def store_command(cmd):
    global last_command_rowid
    lock = threading.Lock()
    lock.acquire() # will block if lock is already held
    try:
        cmd_id = last_command_rowid + 1
        last_command_rowid = cmd_id
    finally:
        lock.release() # release lock, no matter what
        
    conn = sqlite3.connect('queue.db')
    conn.execute ("INSERT INTO commands (rowid, command) VALUES (?,?)", (cmd_id, cmd))    
    conn.commit()
    conn.close()
    
def store_job(job, pid, status):
    global last_job_rowid
    lock = threading.Lock()
    lock.acquire() # will block if lock is already held
    try:
        job_id = last_job_rowid + 1
        last_job_rowid = job_id
    finally:
        lock.release() # release lock, no matter what
        
    conn = sqlite3.connect('queue.db')
    conn.execute ("INSERT INTO jobs (rowid, job, pid, status) VALUES (?,?,?,?)", (job_id, job, pid, status ))    
    conn.commit() 
    conn.close()   
    
def init():
    global last_command_rowid
    global last_job_rowid
    
    # Read vars from ansible file into global vars
    get_xsce_vars()
    
    # Get ansible facts for localhost
    get_ansible_facts()    
    
    # See if queue.db exists and create if not
    # Opening a connection creates if not exist
    if not os.path.isfile('queue.db'):
        conn = sqlite3.connect('queue.db')
        conn.execute ("CREATE TABLE commands (command text)")
        conn.commit()
        conn.execute ("CREATE TABLE jobs (job text, pid integer, status text)")
        conn.commit()
        conn.close()
    else:
        conn = sqlite3.connect('queue.db')
        cur = conn.execute("SELECT max (rowid) from commands")
        row = cur.fetchone()
        if row[0] is not None:
            last_command_rowid = row[0]

        cur = conn.execute("SELECT max (rowid) from jobs")
        row = cur.fetchone()
        if row[0] is not None:
            last_job_rowid = row[0]
        
        cur.close()
        conn.close()

def get_xsce_vars():            
    global default_vars
    global local_vars
    global effective_vars
    
    stream = open(xsce_ansible_path + "/vars/default_vars.yml", 'r')
    default_vars = yaml.load(stream)
    stream.close()
    
    stream = open(xsce_ansible_path + "/vars/local_vars.yml", 'r')
    local_vars = yaml.load(stream)
    stream.close()
    
    # combine vars with local taking precedence
    # exclude derived vars marked by {
    
    for key in default_vars:
        if isinstance(default_vars[key], str):
            if not default_vars[key].find("{"):
                effective_vars[key] = default_vars[key]
        else:
            effective_vars[key] = default_vars[key]
            
    for key in local_vars:
        if isinstance(local_vars[key], str):
            if not local_vars[key].find("{"):
                effective_vars[key] = local_vars[key]       
        else:
            effective_vars[key] = local_vars[key]
                    
def get_ansible_facts():            
    global ansible_facts
       
    rc = subprocess.call(["scripts/ansible_facts.sh"])
    
    stream = open ("/tmp/facts/localhost","r")
    ans = json.load(stream)
    stream.close()
    ansible_facts = ans['ansible_facts']
    
# Now start the application
if __name__ == "__main__":
    main()    

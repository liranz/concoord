"""
@author: denizalti
@note: The Logger Daemon.Receives log messages and prints them.
@date: December 20, 2011
"""
import socket, time, os, sys, select

def collect_input(s):
    msg = ''
    while '\n' not in msg:
        chunk = s.recv(1)
        if chunk == '':
            return False
        msg += chunk
    print_event(msg)
    return True

def print_event(event):
    print "%s: %s" % (time.asctime(time.localtime(time.time())), event.strip())
    
def main():
    try:
        daemonsocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        daemonsocket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        daemonsocket.setsockopt(socket.IPPROTO_TCP,socket.TCP_NODELAY,1)
        daemonsocket.bind(('egs-110.cs.cornell.edu',12000))
        daemonsocket.listen(10)
    except socket.error:
        pass
    print_event("server ready on port %d\n" % 12000)

    socketset = [daemonsocket]
    while True:
        inputready,outputready,exceptready = select.select(socketset,[],socketset,1)
        for s in inputready:
            try:
                if s == daemonsocket:
                    clientsock,clientaddr = daemonsocket.accept()
                    print_event("accepted a connection from address %s\n" % str(clientaddr))
                    socketset.append(clientsock)
                else:
                    if not collect_input(s):
                        socketset.remove(s)
            except socket.error:
                socketset.remove(s)
        for s in exceptready:
            socketset.remove(s)
        
if __name__=='__main__':
    main()

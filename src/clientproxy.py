'''
@author: denizalti
@note: The Client
@date: February 1, 2011
'''
import socket, os, sys, time
from optparse import OptionParser
from threading import Thread, Lock, Condition
from enums import *
from utils import findOwnIP
from connection import ConnectionPool, Connection
from group import Group
from peer import Peer
from message import ClientMessage, Message, PaxosMessage, HandshakeMessage, AckMessage
from command import Command
from pvalue import PValue, PValueSet

parser = OptionParser(usage="usage: %prog -b bootstrap -f file -n serverdomainname -d debug")
parser.add_option("-b", "--boot", action="store", dest="bootstrap", help="address:port tuples separated with commas for bootstrap peers")
parser.add_option("-f", "--file", action="store", dest="filename", default=None, help="inputfile")
parser.add_option("-n", "--name", action="store", dest="name", default=None, help="domain name of the concoord instance")
parser.add_option("-d", "--debug", action="store_true", dest="debug", default=False, help="debug on/off")
(options, args) = parser.parse_args()

REPLY = 0
CONDITION = 1

class Client():
    """Client sends requests and receives responses"""
    def __init__(self, givenbootstraplist, inputfile, domainname, debug):
        self.servicedomainname = domainname
        self.socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        self.bootstraplist = []
        self.initializebootstraplist(givenbootstraplist)
        self.connecttobootstrap()
        myaddr = findOwnIP()
        myport = self.socket.getsockname()[1] 
        self.me = Peer(myaddr,myport,NODE_CLIENT) 
        self.alive = True
        self.clientcommandnumber = 1
        self.commandlistcond = Condition()
        self.commandlist = []
        self.requests = {} # Keeps request:(reply, condition) mappings
        setlogprefix("%s %s" % ('NODE_CLIENT',self.me.getid()))

    def startclientproxy():
        clientloop_thread = Thread(target=self.clientloop)
        clientloop_thread.start()

    def initializebootstraplist(self,givenbootstraplist):
        bootstrapstrlist = givenbootstraplist.split(",")
        for bootstrap in bootstrapstrlist:
            bootaddr,bootport = bootstrap.split(":")
            bootpeer = Peer(bootaddr,int(bootport),NODE_REPLICA)
            self.bootstraplist.append(bootpeer)

    def refreshbootstraplist(self):
        # XXX port number should be changed
        nodes = self.socket.getaddrinfo(self.servicedomainname, 53)
        tmplist = []
        for node in nodes:
            tmplist.append(Peer(node[4][0], int(node[4][1]), NODE_REPLICA))
        self.bootstraplist = tmplist

    def connecttobootstrap(self):
        for bootpeer in self.bootstraplist:
            try:
                print "Connecting to new bootstrap: ", bootpeer.addr,bootpeer.port
                self.socket.close()
                self.socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                self.socket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
                self.socket.connect((bootpeer.addr,bootpeer.port))
                self.conn = Connection(self.socket)
                print "Connected to new bootstrap: ", bootpeer.addr,bootpeer.port
                break
            except socket.error, e:
                print e
                continue

    def invoke_command(self, commandname, args):
        mynumber = self.clientcommandnumber
        self.clientcommandnumber += 1
        commandargs = commandname + " " + args
        newcommand = Command(self.me, mynumber, commandargs)
        with self.commandlistcond:
            self.commandlist.append(newcommand)
            self.requests[newcommand] = (None,Condition())
            self.commandlistcond.notify()
        # Wait for the reply
        while self.requests[newcommand][REPLY] == None:
            self.requests[newcommand][CONDITION].wait()
        # Check if there are exceptions and raise them.
        if self.requests[newcommand][REPLY].replycode == cr_codes[METAREPLY]:
            pass
        elif self.requests[newcommand][REPLY].replycode == cr_codes[EXCEPTION]:
            raise self.requests[newcommand][REPLY].reply
        else:
            return self.requests[newcommand][REPLY].reply
    
    def clientloop(self):
        """Accepts commands from the prompt and sends requests for the commands
        and receives corresponding replies."""
        while self.alive:
            with self.commandlistcond:
                while len(self.commandlist) == 0:
                    self.commandlistcond.wait()
                command = self.commandlist.pop(0)
            cm = ClientMessage(MSG_CLIENTREQUEST, self.me, command)
            replied = False
            #print "Client Message about to be sent:", cm
            starttime = time.time()
            self.conn.settimeout(CLIENTRESENDTIMEOUT)
            
            while not replied:
                success = self.conn.send(cm)
                if not success:
                    currentbootstrap = self.bootstraplist.pop(0)
                    self.bootstraplist.append(currentbootstrap)
                    self.connecttobootstrap()
                    continue
                try:
                    reply = self.conn.receive()
                except:
                    logger("")
                print "received: ", reply
                if reply and reply.type == MSG_CLIENTREPLY and reply.inresponseto == mynumber:
                    if reply.replycode == cr_codes[REJECTED] or reply.replycode == cr_codes[LEADERNOTREADY]:
                        currentbootstrap = self.bootstraplist.pop(0)
                        self.bootstraplist.append(currentbootstrap)
                        self.connecttobootstrap()
                        continue
                    else:
                        replied = True
                        self.requests[newcommand][REPLY] = reply
                        self.requests[newcommand][CONDITION].notify()
                elif reply and reply.type == MSG_CLIENTMETAREPLY and reply.inresponseto == mynumber:
                    pass
                if time.time() - starttime > CLIENTRESENDTIMEOUT:
                    if reply and reply.type == MSG_CLIENTREPLY and reply.inresponseto == mynumber:
                        replied = True
                        self.requests[newcommand][REPLY] = reply
                        self.requests[newcommand][CONDITION].notify()

theClient = Client(options.bootstrap, options.filename, options.name, options.debug)
theClient.clientloop()

  


    
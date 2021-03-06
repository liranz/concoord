'''
@author: Deniz Altinbuken, Emin Gun Sirer
@note: ConCoord Client Proxy
@copyright: See LICENSE
'''
from __future__ import print_function
import os, random, select, socket, sys, threading, time
from threading import Lock
import cPickle as pickle
from concoord.pack import *
from concoord.enums import *
from concoord.utils import *
from concoord.exception import *
from concoord.connection import ConnectionPool, Connection
from concoord.message import *
from concoord.pvalue import PValueSet
import six

try:
    import dns
    import dns.resolver
    import dns.exception
except:
    print("Install dnspython: http://www.dnspython.org/")

class ClientProxy():
    def __init__(self, bootstrap, timeout=60, debug=False, token=None):
        self.debug = debug
        self.timeout = timeout
        self.domainname = None
        self.token = token
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
        self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.writelock = Lock()

        self.bootstraplist = self.discoverbootstrap(bootstrap)
        if len(self.bootstraplist) == 0:
            raise ConnectionError("No bootstrap found")
        if not self.connecttobootstrap():
            raise ConnectionError("Cannot connect to any bootstrap")
        myaddr = findOwnIP()
        myport = self.socket.getsockname()[1]
        self.me = Peer(myaddr, myport, NODE_CLIENT)
        self.commandnumber = random.randint(1, sys.maxint)

    def _getipportpairs(self, bootaddr, bootport):
        for node in socket.getaddrinfo(bootaddr, bootport, socket.AF_INET, socket.SOCK_STREAM):
            yield (node[4][0],bootport)

    def getbootstrapfromdomain(self, domainname):
        tmpbootstraplist = []
        try:
            answers = dns.resolver.query('_concoord._tcp.'+domainname, 'SRV')
            for rdata in answers:
                for peer in self._getipportpairs(str(rdata.target), rdata.port):
                    if peer not in tmpbootstraplist:
                        tmpbootstraplist.append(peer)
        except (dns.resolver.NXDOMAIN, dns.exception.Timeout):
            if self.debug: print ("Cannot resolve name")
        return tmpbootstraplist

    def discoverbootstrap(self, givenbootstrap):
        tmpbootstraplist = []
        try:
            for bootstrap in givenbootstrap.split(","):
                bootstrap = bootstrap.strip()
                # The bootstrap list is read only during initialization
                if bootstrap.find(":") >= 0:
                    bootaddr,bootport = bootstrap.split(":")
                    for peer in self._getipportpairs(bootaddr, int(bootport)):
                        if peer not in tmpbootstraplist:
                            tmpbootstraplist.append(peer)
                else:
                    self.domainname = bootstrap
                    tmpbootstraplist = self.getbootstrapfromdomain(self.domainname)
        except ValueError:
            if self.debug: print ("bootstrap usage: ipaddr1:port1,ipaddr2:port2 or domainname")
            self._graceexit()
        return tmpbootstraplist

    def connecttobootstrap(self):
        connected = False
        if self.debug: print ("connecttobootstrap called.")
        for boottuple in self.bootstraplist:
            try:
                self.socket.close()
                self.socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                self.socket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
                self.socket.connect(boottuple)
                self.conn = Connection(self.socket)
                self.conn.settimeout(CLIENTRESENDTIMEOUT)
                self.bootstrap = boottuple
                connected = True
                if self.debug: print ("Connected to new bootstrap: ", boottuple)
                break
            except socket.error, e:
                if self.debug: print ("Socket.Error: ", e)
                continue
        return connected

    def trynewbootstrap(self):
        if self.domainname:
            self.bootstraplist = self.getbootstrapfromdomain(self.domainname)
        else:
            oldbootstrap = self.bootstraplist.pop(0)
            self.bootstraplist.append(oldbootstrap)
        return self.connecttobootstrap()

    def invoke_command(self, *args):
        # create a request descriptor
        resend = True
        sendcount = -1
        lastreplycode = -1
        self.commandnumber += 1
        clientmsg = create_message(MSG_CLIENTREQUEST, self.me,
                                   {FLD_PROPOSAL: Proposal(self.me, self.commandnumber, args),
                                    FLD_TOKEN: self.token,
                                    FLD_CLIENTBATCH: False})
        if self.debug: print ("In invoke command. clientmessage is : ", clientmsg)
        while True:
            sendcount += 1
            clientmsg[FLD_SENDCOUNT] = sendcount
            # send the clientrequest
            if resend:
                success = self.conn.send(clientmsg)
                if self.debug: print ("Sent msg to bootstrap. success is : ", success)
                if not success:
                    if self.debug: print ("Sent msg to bootstrap failed, reconfiguring")
                    self.reconfigure()
                    continue
                resend = False
        # Receive reply
            try:
                for reply in self.conn.received_bytes():
                    if self.debug: print ("reply received: ", reply, reply.type)
                    if reply and reply.type == MSG_CLIENTREPLY:
                        if self.debug: print ("reply received: MSG_CLIENTRPLY")
                        if reply.replycode == CR_OK:
                            if self.debug: print ("reply received: MSG_CLIENTRPLY, replycode is CR_OK")
                            return reply.reply
                        elif reply.replycode == CR_UNBLOCK:
                            if self.debug: print ("reply received: MSG_CLIENTRPLY, replycode is CR_UNBLOCK")
                            # actionable response, wake up the thread
                            assert lastreplycode == CR_BLOCK, "unblocked thread not previously blocked"
                            return reply.reply
                        elif reply.replycode == CR_EXCEPTION:
                            if self.debug: print ("reply received: MSG_CLIENTRPLY, replycode is CR_EXCEPTION reply is %r" %(reply.reply,))
                            if six.PY2:
                                raise Exception(pickle.loads(reply.reply))
                            else:
                                exc_reply = bytes(reply.reply, 'latin1')
                                raise pickle.loads(exc_reply)
                        elif reply.replycode == CR_INPROGRESS or reply.replycode == CR_BLOCK:
                            if self.debug: print ("reply received: MSG_CLIENTRPLY, replycode is CR_BLOCK or CR_INPROGRESS", reply.replycode)
                            # the thread is already waiting, no need to do anything
                            lastreplycode = reply.replycode
                            # go wait for another message
                            continue
                        elif reply.replycode == CR_REJECTED or reply.replycode == CR_LEADERNOTREADY:
                            if self.debug: print ("reply received: MSG_CLIENTRPLY, replycode is CR_REJECTED or CR_LEADERNOTREADY")
                            resend = True
                            self.reconfigure()
                            continue
                        else:
                            print ("Unknown Client Reply Code.")
            except ConnectionError as e:
                if self.debug: print ("CAUGHT ConnectionError, will reconfigure and try again. exception: %r %r" %(e,str(e) ) )
                resend = True
                self.reconfigure()
                continue
            except KeyboardInterrupt:
                self._graceexit()

    def reconfigure(self):
        if self.debug: print ("reconfigure called.")
        if not self.trynewbootstrap():
            raise ConnectionError("Cannot connect to any bootstrap")

    def _graceexit(self):
        os._exit(0)

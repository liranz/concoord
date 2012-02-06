'''
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Automatically generated OpenReplica coordination object proxy.
@date: August 1, 2011
@copyright: See COPYING.txt
'''
from concoord.clientproxy import *

class OpenReplicaCoordProxy():
    def __init__(self, bootstrap):
        self.proxy = ClientProxy(bootstrap)

    def addnodetosubdomain(self, subdomain, node):
        return self.proxy.invoke_command("addnodetosubdomain", subdomain, node)

    def delnodefromsubdomain(self, subdomain, node):
        return self.proxy.invoke_command("delnodefromsubdomain", subdomain, node)

    def delsubdomain(self, subdomain):
        return self.proxy.invoke_command("delsubdomain", subdomain)

    def getnodes(self, subdomain):
        return self.proxy.invoke_command("getnodes", subdomain)

    def getsubdomains(self):
        return self.proxy.invoke_command("getsubdomains")

    def __str__(self):
        return self.proxy.invoke_command("__str__")
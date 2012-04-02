'''
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Nameserver coordination object proxy
@copyright: See LICENSE
'''
from concoord.clientproxy import ClientProxy

class NameserverCoord:
    def __init__(self, bootstrap):
        self.proxy = ClientProxy(bootstrap)
        
    def __concoordinit__(self):
        return self.proxy.invoke_command('__init__')

    def addnodetosubdomain(self, subdomain, nodetype, node):
        return self.proxy.invoke_command('addnodetosubdomain', subdomain, nodetype, node)

    def delsubdomain(self, subdomain):
        return self.proxy.invoke_command('delsubdomain', subdomain)

    def delnodefromsubdomain(self, subdomain, nodetype, node):
        return self.proxy.invoke_command('delnodefromsubdomain', subdomain, nodetype, node)

    def updatesubdomain(self, subdomain, nodes):
        print subdomain
        print nodes
        return self.proxy.invoke_command('updatesubdomain', subdomain, nodes)

    def getnodes(self, subdomain):
        return self.proxy.invoke_command('getnodes', subdomain)

    def getsubdomains(self):
        return self.proxy.invoke_command('getsubdomains')

    def _reinstantiatefromstr(self, state):
        return self.proxy.invoke_command('_reinstantiatefromstr', state)

    def __str__(self):
        return self.proxy.invoke_command('__str__')
'''
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Planet Lab initializer that handles node/slice operations
@date: August 1, 2011
@copyright: See COPYING.txt
'''
import xmlrpclib
import sys

SLICENAME = 'cornell_openreplica'
s = xmlrpclib.ServerProxy('https://www.planet-lab.org/PLCAPI/', allow_none=True)
# Specify password authentication
auth = {'Username': 'denizalti@gmail.com',
        'AuthString': '11235813',
        'AuthMethod': 'password'}
authorized = s.AuthCheck(auth)
if not authorized:
    print 'Authorization failed!'

def listallnodes():
    print 'Getting all nodes!'
    all_nodes = s.GetNodes(auth)
    nodes = []
    for node in all_nodes:
        nodes.append(node['hostname'])
        print node['hostname']
    return nodes

def writeallnodestofile():
    f = open("plnodes.txt", 'w')
    all_nodes = s.GetNodes(auth)
    for node in all_nodes:
        f.write(node['hostname']+"\n")
    f.close()

def addnodes(nodes):
    slice_id = s.GetSlices(auth, [SLICENAME], ['slice_id'])[0]['slice_id']
    s.AddSliceToNodes(auth, slice_id, nodes)

def shownodes():
    node_ids = s.GetSlices(auth, [SLICENAME], ['node_ids'])[0]['node_ids']
    node_hostnames = [node['hostname'] for node in s.GetNodes(auth, node_ids, ['hostname'])]
    print node_hostnames

def getallnodes():
    all_nodes = s.GetNodes(auth)
    nodenames = []
    for node in all_nodes:
        nodenames.append(node['hostname'])
    return nodenames

def main():
    addnodes(listallnodes())
    
if __name__ == '__main__':
    sys.exit(main())


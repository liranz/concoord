# DNS Packet
### MAC Header : 14 bytes
### IP Header : 20 bytes
### UDP Header : 8 bytes
### DNS Section : 32 bytes
##### DNS Query : ID, Flags, Questions, AnswerRRs, Authority RRs, AdditionalRRs
##### DNS Response :
import sys

IPINDEX = 14
UDPINDEX = 34
DNSINDEX = 42
AQUERY = "\x00\x01"
NSQUERY = "\x00\x10"

class DNSPacket:
  def __init__(self, data):
    self.data = data
    self.mac = data[:IPINDEX]
    self.ip = data[IPINDEX:UDPINDEX]
    self.udp = data[UDPINDEX:DNSINDEX]
    self.dns = data[DNSINDEX:]
    self.query = DNSQuery(self.dns)

class DNSQuery:
  def __init__(self, data):
    self.data = data #"\x5f\x89\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x04\x74\x30\x34\x61\x05\x68\x79\x70\x65\x6d\x03\x63\x6f\x6d\x00\x00\x01\x00\x01"
    self.ID = self.data[:2]
    self.opcode = (ord(self.data[2]) >> 3) & 15   # 4-bit Opcode: 0|1|2
    self.questions = ord(self.data[4])*16 + ord(self.data[5])
    self.queries = self.data[12:]
    self.domain = ''

    if self.opcode == 0:                     # standard query (QUERY)
      index = 12
      length = ord(self.data[index])
      while length != 0:
        self.domain += self.data[index+1:index+length+1]+'.'
        index += length+1
        length = ord(self.data[index])
      self.querytype = self.data[index+1:index+3]
    if self.querytype == AQUERY:
      print "AQuery for %s" % self.domain

  def create_a_response(self, peers, auth=False):
    response=''
    if self.domain:
      if auth:
        response += self.ID + "\x85"
      else:
        response += self.ID + "\x81"                                     # ID + Flags: isResponse, Opcode, Authoritative, Truncated, RecursionDesired
      response += "\x80"                                                 # Flags: RecursionAvail
      response += self.data[4:6] + self.data[4:6] + '\x00\x00\x00\x00'   # Question Count + Answer Count + Authority RRs + Additional RRs
      response += self.data[12:]                                         # Original Domain Name Question
      response += '\xc0\x0c'                                             # Pointer to domain name
      response += AQUERY                                                 # Response type: A (Host Address)
      response += '\x00\x01'                                             # Class
      response += '\x00\x00\x0b\xa0'                                     # TTL
      response += '\x00'                                             
      response += chr(int(len(peers)*4))                                 # Data length : 4 bytes*numpeers
      for peer in peers:
        addr,port = peer.split(':')
        response += str.join('',map(lambda x: chr(int(x)), addr.split('.'))) # 4bytes of IP
    return response

  def create_ns_response(self, authns, auth=False):
    response=''
    if self.domain:
      response += self.ID + "\x81\x80"                                   # ID + Flags: isResponse, RecursionDesired, RecursionAvail
      response += self.data[4:6] + self.data[4:6] + '\x00\x00\x00\x00'   # Question Count + Answer Count + Authority RRs + Additional RRs
      response += self.data[12:]                                         # Original Domain Name Question
      response += '\xc0\x0c'                                             # Pointer to domain name
      response += NSQUERY                                                # Response type: NS (Authoritative Name Server)
      response += '\x00\x01'                                             # Class
      response += '\x00\x00\x0b\xa0'                                     # TTL
      response += '\x00\x04'                                             # Data length : 4 bytes
      response += str.join('',map(lambda x: chr(int(x)), authns.split('.'))) # 4bytes of IP
    return response

  def create_error_response(self,authns):
    response=''
    if self.domain:
      response += self.ID + "\x81\x83"                                   # ID + Flags: isResponse, RecursionDesired, RecursionAvail, 3: NameError
      response += self.data[4:6] + self.data[4:6] + '\x00\x00\x00\x00'   # Question Count + Answer Count + Authority RRs + Additional RRs
      response += self.data[12:]                                         # Original Domain Name Question
      response += '\xc0\x0c'                                             # Pointer to domain name
      response += NSQUERY                                                # Response type: NS (Authoritative Name Server)
      response += '\x00\x01'                                             # Class
      response += '\x00\x00\x0b\xa0'                                     # TTL
      response += '\x00\x04'                                             # Data length : 4 bytes
      response += str.join('',map(lambda x: chr(int(x)), authns.split('.'))) # 4bytes of IP
    return response

#def main():
#    peers = ["173.244.195.44"]
#    dnsquery = DNSPacket(testquery)
#    dnsresponse = DNSPacket(testresponse)
#    print dnsquery.query.create_response(peers) == dnsresponse.dns

#if __name__=='__main__':
#    main()   
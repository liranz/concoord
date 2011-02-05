import hashlib
import socket
import random
import struct
from message import *

class scoutReply():
    def __init__(self,replyLock,replyCondition,giventype=0,givenballotnumber=0,givenpvalueset=None):
        self.type = giventype
        self.ballotnumber = givenballotnumber
        self.pvalueset = givenpvalueset
        self.replyLock = replyLock
        self.replyCondition = replyCondition
        
    def __str__(self):
        return "%s:\nballotnumber: %s\npvalueset:%s\n" % (scout_names[self.type],str(self.ballotnumber),self.pvalueset)
        
class commanderReply():
    def __init__(self,replyLock,replyCondition,giventype=0,givenballotnumber=0,givencommandnumber=0):
        self.type = giventype
        self.ballotnumber = givenballotnumber
        self.commandnumber = givencommandnumber
        self.replyLock = replyLock
        self.replyCondition = replyCondition

    def __str__(self):
        return "%s\nballotnumber: %s\ncommandnumber: %d" % (commander_names[self.type],str(self.ballotnumber),self.commandnumber)
"""
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Condition Coordination Object
@copyright: See LICENSE
"""
from threading import RLock
from concoord.exception import *
from drlock import DRlock
from dlock import DLock
    
class DCondition():
    def __init__(self):
        self.atomic = RLock()
        self.lock = DLock()
        self.__waiters = []
    
    def acquire(self, _concoord_command):
        try:
            return self.lock.acquire(kwargs)
        except UnusualReturn:
            raise UnusualReturn

    def release(self, _concoord_command):
        return self.lock.release(kwargs)

    def wait(self, _concoord_command):
        # put the caller on waitinglist and take the lock away
        with self.atomic:
            if self.lock.locked == True and self.lock.holder == _concoord_command.client:
                self.__waiters.append(_concoord_command)
                self.lock.release(kwargs)
                raise UnusualReturn
            else:
                raise RuntimeError("cannot wait on un-acquired lock")

    def notify(self, _concoord_command):
        # Notify the next client on the wait list
        with self.atomic:
            if self.lock.locked == True and self.lock.holder == _concoord_command.client:
                waitcommand = self.__waiters.pop(0)
                # To make sure that the client that will be unblocked has the lock we'll add the client to the lock queue.
                self.lock.queue.append(waitcommand)
            else:
                raise RuntimeError("cannot notify on un-acquired lock")         

    def notifyAll(self, _concoord_command):
        # Notify every client on the wait list
        with self.atomic:
            if self.lock.locked == True and self.lock.holder == _concoord_command.client:
                for waitcommand in self.__waiters:
                    self.lock.queue.append(waitcommand)
            else:
                raise RuntimeError("cannot notify on un-acquired lock")   

    def __str__(self):
        return '<concoord.threadingobjects.dcondition object>'


from queue import Queue
from ..modules.DataType import AlertData
class LongPollingModules:
    __instance = None
    __isInitialized = False
    __long_pollings = {}

    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = super().__new__(cls)
        return cls.__instance
    def __init__(self):
        if not self.__isInitialized: 
            self.__isInitialized = True

    def isNotHavingClients(self)-> bool:
        if len(self.__long_pollings) == 0 :
            return True
        return False

    def addClientId(self, client_id):
        if client_id not in self.__long_pollings:
            self.__long_pollings[client_id] = Queue()

    def removeClientId(self, client_id):
        self.__long_pollings.pop(client_id)

    def getLongPollingOfSpecifiedClient(self, client_id):
        return self.__long_pollings[client_id]
    
    def sendMsgToClient(self, client_id, data: AlertData):
        if client_id in self.__long_pollings:
            self.__long_pollings[client_id].put(data)
            print("check queue of: ", client_id, "is empty: ", self.__long_pollings[client_id].empty())


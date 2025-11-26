import asyncio
import time
from AnalysisTask import AnalysisTask
class Analysis:
    __instance = None
    __isInitialized = False
    __tasks_dict = {}

    #Khoảng thời gian sau khi rời đi
    LEAVING_DURATION = 5

    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = super().__new__(cls)
        return cls.__instance

            
    def startTrackingStranger(self, id_stranger):
        self.__tasks_dict[id_stranger] = AnalysisTask(id_stranger, 
            on_complete=lambda:self.__tasks_dict.pop(id_stranger))
    
    def pauseTrackingStranger(self, id_stranger):
        task = self.__tasks_dict.get(id_stranger)
        if not task is None:
            task.pause()

    def resumeTrackingStranger(self, id_stranger):
        task = self.__tasks_dict.get(id_stranger)
        if not task is None:
            task.resume()

    def stopTrackingStranger(self, id_stranger):
        task = self.__tasks_dict.get(id_stranger)
        if not task is None:
            task.cancel()
            self.__tasks_dict.pop(id_stranger)
    def checkManageredTasks(self):
        print(self.__tasks_dict)


# demo các trường hợp xảy ra :
# + phát hiện người lạ đứng quá thời gian cho phép
# + người lạ rời khỏi camera, sau đó lại quay lại sau một khoảng thời gian ngắn
# + người lạ rời khỏi camera và đi hẳn

#case 1: trường hợp người lạ đứng quá thời gian cho phép
async def case_1():
    analysis = Analysis()
    id_stranger = 0

    #phát hiện người lạ
    analysis.startTrackingStranger(id_stranger)

    await asyncio.sleep(12)
    print("done!!")
    #check release memory
    analysis.checkManageredTasks()


#case 2: trường hợp người lạ rời khỏi camera, sau đó lại quay lại sau một khoảng thời gian ngắn
async def case_2():
    analysis = Analysis()
    id_stranger = 0

    #phát hiện người lạ
    analysis.startTrackingStranger(id_stranger)
    await asyncio.sleep(8)

    #sau khi đứng 8 giây, thì camera phát hiện người lạ rời đi
    analysis.pauseTrackingStranger(id_stranger)

    #sau khoảng 5 s sau lại thấy người lạ đó lại quay lại
    await asyncio.sleep(5)
    analysis.resumeTrackingStranger(id_stranger)

    await asyncio.sleep(5)
    print("done!!")
    #check release memory
    analysis.checkManageredTasks()


#case 3: người lạ rời khỏi camera và đi hẳn
async def case_3():
    analysis = Analysis()
    id_stranger = 0

    #phát hiện người lạ
    analysis.startTrackingStranger(id_stranger)
    await asyncio.sleep(8)

    #sau khi đứng 8 giây, thì camera phát hiện người lạ rời đi
    analysis.pauseTrackingStranger(id_stranger)

    #sau khoảng 5s sau coi như có vẻ người lạ đi rồi 
    await asyncio.sleep(5)
    analysis.stopTrackingStranger(id_stranger)

    await asyncio.sleep(5)
    print("done!!")
    #check release memory
    analysis.checkManageredTasks()


asyncio.run(case_1())

   
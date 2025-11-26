import asyncio
import time

class AnalysisTask:

     # Khoảng thời gian trước khi cảnh báo
    LEGAL_DURATION = 10

    def __init__(self, id_stranger, on_complete = None):
        self.paused = asyncio.Event()
        self.id_stranger = id_stranger
        self.task = asyncio.create_task(self.run())
        self.paused.set()
        self.origin_start_time = time.time()  
        self.start_time = time.time()
        self.end_time = time.time()
        self.on_complete = on_complete
        self.task.add_done_callback( lambda f: print(f"Tracking stranger with id: {id_stranger}", 
                                     f"is done after: {self.end_time - self.origin_start_time} seconds"))



    async def run(self):
        count = 1
        try:
            while self.end_time - self.start_time <= self.LEGAL_DURATION:
                await self.paused.wait() 
                await asyncio.sleep(1)
                print("check count: ", count)
                self.end_time = time.time()
                count += 1

            # alert to user
            print("Alert!!")
            self.on_complete()
        except asyncio.CancelledError:
            print("stranger with id ", self.id_stranger, " is left!!")
            pass
       

    def pause(self):
        print("pause tracking stranger with id: ", self.id_stranger)
        self.paused.clear() 

    def resume(self):
        print("resume tracking stranger with id: ", self.id_stranger)
        duration = self.end_time - self.start_time
        self.start_time = time.time() - duration
        self.end_time = time.time()
        print("check current end time: ", self.end_time)
        print("check current start time: ", self.start_time)
        print("check current duration: ", {self.end_time - self.start_time})
        self.paused.set() 

    def cancel(self):
        print("cancel Tracking stranger with id: ", self.id_stranger)
        self.task.cancel()

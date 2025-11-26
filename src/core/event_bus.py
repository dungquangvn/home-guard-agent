import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Dict, List
from queue import Queue

class EventBus:
    def __init__(self):
        self.handlers = {}      # event_name → [callback]
        self.queues = {}        # event_name → Queue
        self.threads = {}       # event_name → [thread]

    def on(self, event_name: str, callback):
        # Tạo queue cho event_name nếu chưa có
        if event_name not in self.queues:
            self.queues[event_name] = Queue()
            self.handlers[event_name] = []
            self.threads[event_name] = []

        self.handlers[event_name].append(callback)

        # Tạo luôn worker thread cho callback này
        t = threading.Thread(target=self._worker, args=(event_name, callback), daemon=True)
        self.threads[event_name].append(t)
        t.start()

    def _worker(self, event_name, callback):
        """Worker chạy suốt đời, xử lý event từ queue."""
        q = self.queues[event_name]

        while True:
            evt = q.get()      # blocking, không tốn CPU
            try:
                callback(evt)
            except Exception as e:
                print(f"[EventBus] Error in handler {callback}: {e}")

    def emit(self, events):
        """Main chỉ push event vào Queue — NON-BLOCK"""
        for evt in events:
            evt_name = evt["event"]
            if evt_name in self.queues:
                self.queues[evt_name].put(evt)


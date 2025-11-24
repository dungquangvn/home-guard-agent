import asyncio
from collections import defaultdict
from typing import Callable, Any, Dict, List


class EventBus:
    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = defaultdict(list)

    def on(self, event_type: str, handler: Callable):
        """Đăng ký handler khi có event."""
        self._handlers[event_type].append(handler)

    async def emit(self, event_type: str, data: Dict[str, Any]):
        """Kích hoạt tất cả handler gán với event."""
        if event_type not in self._handlers:
            return

        tasks = []
        for handler in self._handlers[event_type]:

            # Nếu handler là async
            if asyncio.iscoroutinefunction(handler):
                tasks.append(handler(data))
            else:
                # Non-async handler chạy trong loop
                loop = asyncio.get_event_loop()
                tasks.append(loop.run_in_executor(None, handler, data))

        # Chạy tất cả handler song song
        if tasks:
            await asyncio.gather(*tasks)
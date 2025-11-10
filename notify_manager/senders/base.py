from abc import ABC, abstractmethod
from typing import Dict, Any


class AbstractSender(ABC):
    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()

    @abstractmethod
    async def connect(self) -> None:
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        pass

    @abstractmethod
    async def send_notify(self, *args, **kwargs) -> Dict[str, Any]:
        pass

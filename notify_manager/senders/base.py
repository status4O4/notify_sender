from abc import ABC, abstractmethod
from typing import Dict, Any


class AbstractSender(ABC):
    """
    Абстрактный базовый класс для сендеров.
    Реализует паттерн контекстного менеджера для экономии ресурсов - соединения
    устанавливаются только на время отправки уведомлений, так как сервис работает
    эпизодически и не требует постоянно открытых соединений.

    (соединения используются повторно если несколько уведомлений пытаются
    отправиться в одно время).
    """

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

    @abstractmethod
    async def test_connection(self) -> bool:
        pass

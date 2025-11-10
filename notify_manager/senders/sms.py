import asyncio
import aiohttp
from typing import Optional
from .base import AbstractSender


class SMSSender(AbstractSender):
    def __init__(self, username: str, password: str, sender: str = "SMSSender"):
        self.username: str = username
        self.password: str = password
        self.sender: str = sender
        self._session: Optional[aiohttp.ClientSession] = None
        self.base_url: str = "https://smsc.ru/rest/send/"
        self._reference_count: int = 0
        self._lock: asyncio.Lock = asyncio.Lock()

    async def connect(self) -> None:
        async with self._lock:
            if self._reference_count == 0:
                self._session = aiohttp.ClientSession()
            self._reference_count += 1

    async def disconnect(self) -> None:
        async with self._lock:
            if self._reference_count > 0:
                self._reference_count -= 1
                if self._reference_count == 0 and self._session:
                    try:
                        await self._session.close()
                    except Exception:
                        pass
                    finally:
                        self._session = None

    async def send_notify(self, phone: str, notify: str) -> dict:
        data = {
            "login": self.username,
            "psw": self.password,
            "phones": phone,
            "mes": notify,
            "sender": self.sender,
            "fmt": 3,
        }

        try:
            if not self._session:
                raise RuntimeError(
                    "SMSSender должен использоваться как контекстный менеджер"
                )
            async with self._session.post(self.base_url, json=data) as response:
                response_data = await response.json()
                error = response_data.get("error", None)
                if response.status == 200 and not error:
                    return {
                        "success": True,
                        "message": "SMS отправлен успешно",
                        "error": None,
                    }
                else:
                    return {
                        "success": False,
                        "message": f"Ошибка отправки SMS: {error}",
                        "error": response.status,
                    }

        except Exception as e:
            return {
                "success": False,
                "message": f"Ошибка отправки SMS: {str(e)}",
                "error": e,
            }

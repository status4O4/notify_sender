import asyncio
from typing import Optional
from aiogram import Bot
from .base import AbstractSender


class TgSender(AbstractSender):
    def __init__(self, token: str):
        self.token: str = token
        self._session: Optional[Bot] = None
        self._reference_count: int = 0
        self._lock: asyncio.Lock = asyncio.Lock()

    async def connect(self) -> None:
        async with self._lock:
            if self._reference_count == 0:
                self._session = Bot(token=self.token)
            self._reference_count += 1

    async def disconnect(self) -> None:
        async with self._lock:
            if self._reference_count > 0:
                self._reference_count -= 1
                if self._reference_count == 0 and self._session:
                    try:
                        await self._session.session.close()
                    except Exception:
                        pass
                    finally:
                        self._session = None

    async def send_notify(self, user_id: int, notify: str):
        try:
            if not self._session:
                raise RuntimeError(
                    "TgSender должен использоваться как контекстный менеджер"
                )
            await self._session.send_message(chat_id=user_id, text=notify)

            return {
                "success": True,
                "message": "Tg отправлен успешно",
                "error": None,
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Ошибка отправки Tg: {str(e)}",
                "error": e,
            }

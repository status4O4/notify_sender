import logging
import asyncio
from typing import Optional
from aiogram import Bot
from .base import AbstractSender


logger = logging.getLogger(__name__)


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
                logger.info(
                    f"TgSender session created. reference_count={self._reference_count + 1}"
                )
            else:
                logger.info(
                    f"TgSender session received. reference_count={self._reference_count + 1}"
                )
            self._reference_count += 1

    async def disconnect(self) -> None:
        # await asyncio.sleep(1)
        async with self._lock:
            if self._reference_count > 0:
                self._reference_count -= 1
                if self._reference_count == 0 and self._session:
                    try:
                        await self._session.session.close()
                    except Exception as err:
                        logging.warning(err)
                    finally:
                        self._session = None
                        logger.info(
                            f"TgSender session closed. reference_count={self._reference_count}"
                        )

    async def test_connection(self) -> bool:
        try:
            if not self._session:
                return False

            await self._session.get_me()
            return True
        except Exception as err:
            logger.error(err)
            return False

    async def send_notify(self, user_id: int, notify: str):
        try:
            if not self._session:
                raise RuntimeError("Use TgSender as a context manager!!!!!")
            await self._session.send_message(chat_id=user_id, text=notify)

            result = {
                "success": True,
                "message": "TG sent successfully",
                "error": None,
            }
            logger.info(result.get("message"))
            return result

        except Exception as err:
            logger.error(err)
            return {
                "success": False,
                "message": f"Ошибка отправки Tg: {str(err)}",
                "error": err,
            }

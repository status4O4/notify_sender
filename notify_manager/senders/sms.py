import logging
import asyncio
import aiohttp
from typing import Optional
from .base import AbstractSender

logger = logging.getLogger(__name__)


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
                logger.info(
                    f"SMSSender session created. reference_count={self._reference_count + 1}"
                )
            else:
                logger.info(
                    f"SMSSender session received. reference_count={self._reference_count + 1}"
                )
            self._reference_count += 1

    async def disconnect(self) -> None:
        async with self._lock:
            if self._reference_count > 0:
                self._reference_count -= 1
                if self._reference_count == 0 and self._session:
                    try:
                        await self._session.close()
                    except Exception as err:
                        logging.warning(err)
                    finally:
                        self._session = None
                        logger.info(
                            f"SMSSender session closed. reference_count={self._reference_count}"
                        )

    async def test_connection(self) -> bool:
        try:
            if not self._session:
                return False
            data = {
                "login": self.username,
                "psw": self.password,
                "phones": "",
                "mes": "",
                "id": "",
            }
            async with self._session.post(self.base_url, json=data) as response:
                response_data = await response.json()
                error = response_data.get("error", None)
                if response.status == 200 and not error:
                    return True
                else:
                    logging.error(error)
                    return False
        except Exception as err:
            logging.error(err)
            return False

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
                raise RuntimeError("Use SMSSender as a context manager!!!!!")
            async with self._session.post(self.base_url, json=data) as response:
                response_data = await response.json()
                error = response_data.get("error", None)
                if response.status == 200 and not error:
                    result = {
                        "success": True,
                        "message": "SMS sent successfully",
                        "error": None,
                    }
                    logger.info(result.get("message"))
                    return result
                else:
                    logger.error(error)
                    return {
                        "success": False,
                        "message": f"Failed to send SMS: {str(error)}",
                        "error": response.status,
                    }

        except Exception as err:
            logger.error(err)
            return {
                "success": False,
                "message": f"Ошибка отправки SMS: {str(err)}",
                "error": err,
            }

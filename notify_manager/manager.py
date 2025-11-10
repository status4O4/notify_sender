import logging
from typing import Dict
from enum import Enum

from dataclasses import asdict

from .senders.base import AbstractSender
from .senders.email import EmailSender
from .senders.sms import SMSSender
from .senders.tg import TgSender
from .config.config import app_config

logger = logging.getLogger(__name__)


class SenderType(Enum):
    EMAIL = "email"
    SMS = "sms"
    TELEGRAM = "telegram"


class NotifyManager:
    SENDER_CLASSES = {
        SenderType.EMAIL: EmailSender,
        SenderType.SMS: SMSSender,
        SenderType.TELEGRAM: TgSender,
    }

    def __init__(self):
        self._senders: Dict[SenderType, AbstractSender] = {}
        self._initialized = False
        self._config = app_config

    async def initialize(self) -> None:
        """
        Инициализирует все доступные отправители уведомлений.
        Тестирует подключение для каждого типа и добавляет только рабочие.
        Вызывает исключение, если ни один отправитель не инициализирован.
        """
        if self._initialized:
            return

        for sender_type in SenderType:
            try:
                config = asdict(app_config[sender_type.value])
                sender = self.SENDER_CLASSES[sender_type](**config)
                is_connected = None
                try:
                    async with sender as sn:
                        is_connected = await sn.test_connection()

                        if is_connected:
                            self._senders[sender_type] = sender
                        else:
                            logger.warning(
                                f"Failed to establish connection with {sender_type}"
                            )
                except Exception as err:
                    logger.warning(
                        f"Error to establish connection with {sender_type}: {err}"
                    )
            except Exception as err:
                logger.error(err)
        if not len(self._senders):
            raise RuntimeError("Failed to initialize services")

        logger.info(
            f"Notify manager has been initialized. Current senders: {[sender.value for sender in self._senders]}"
        )
        self._initialized = True

    async def send_notify(self, message: str, tg_id: int, email: str, phone: str):
        """
        Отправляет уведомление через доступные каналы (email/SMS/Telegram)
        до первой успешной отправки. Возвращает результат отправки.
        """
        result = None

        for sender_key in self._senders:
            async with self._senders[sender_key] as sender:
                match sender_key:
                    case SenderType.EMAIL:
                        result = await sender.send_notify(
                            to_addrs=[email],
                            subject="notify",
                            notify=message,
                        )
                    case SenderType.SMS:
                        result = await sender.send_notify(
                            phone=phone,
                            notify=message,
                        )
                    case SenderType.TELEGRAM:
                        result = await sender.send_notify(user_id=tg_id, notify=message)

            if not result.get("error") and result:
                return result

        return result


async def get_notify_manager() -> NotifyManager:
    notify_manager = NotifyManager()
    await notify_manager.initialize()
    return notify_manager

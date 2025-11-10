from typing import Dict
from enum import Enum

from dataclasses import asdict

from .senders.base import AbstractSender
from .senders.email import EmailSender
from .senders.sms import SMSSender
from .senders.tg import TgSender
from .config.config import app_config


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

    def initialize(self) -> None:
        if self._initialized:
            return

        for sender_type in SenderType:
            try:
                config = asdict(app_config[sender_type.value])
                self._senders[sender_type] = self.SENDER_CLASSES[sender_type](**config)
            except Exception:
                pass
        self._initialized = True

    async def send_notify(self, message: str, tg_id: int, email: str, phone: str):
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


def get_notify_manager() -> NotifyManager:
    notify_manager = NotifyManager()
    notify_manager.initialize()
    return notify_manager

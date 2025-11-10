from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class EmailConfig:
    host: str = os.getenv("EMAIL_NOTIFIER_HOST", "smtp.yandex.ru")
    port: int = int(os.getenv("EMAIL_NOTIFIER_PORT", "465"))
    username: str = os.getenv("EMAIL_NOTIFIER_LOGIN", "")
    password: str = os.getenv("EMAIL_NOTIFIER_PASS", "")
    use_tls: bool = True


@dataclass(frozen=True)
class SMSConfig:
    username: str = os.getenv("SMS_NOTIFIER_LOGIN", "your_login")
    password: str = os.getenv("SMS_NOTIFIER_PASSWORD", "")
    sender: str = os.getenv("SMS_NOTIFIER_SENDER", "")


@dataclass(frozen=True)
class TelegramConfig:
    token: str = os.getenv("TG_NOTIFIER_BOT_TOKEN", "")


class AppConfig:
    def __init__(self):
        self.email: EmailConfig = EmailConfig()
        self.sms: SMSConfig = SMSConfig()
        self.telegram: TelegramConfig = TelegramConfig()
        self.logger_name = "uvicorn"

    def __getitem__(self, config_type: str):
        config_type = config_type.lower()
        if config_type in ["email", "mail"]:
            return self.email
        elif config_type in ["sms", "text"]:
            return self.sms
        elif config_type in ["telegram", "tg"]:
            return self.telegram
        else:
            raise KeyError(f"Unknown config type: {config_type}")


app_config = AppConfig()

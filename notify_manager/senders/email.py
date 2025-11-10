import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import aiosmtplib
from typing import List, Dict, Any, Optional
from .base import AbstractSender


class EmailSender(AbstractSender):
    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        port: int = 465,
        use_tls: bool = True,
        timeout: int = 10,
    ):
        self.host: str = host
        self.port: int = port
        self.username: str = username
        self.password: str = password
        self.use_tls: bool = use_tls
        self.timeout: int = timeout
        self._session: Optional[aiosmtplib.smtp.SMTP] = None
        self._reference_count: int = 0
        self._lock: asyncio.Lock = asyncio.Lock()

    async def connect(self) -> None:
        async with self._lock:
            if self._reference_count == 0:
                self._session = aiosmtplib.SMTP(
                    hostname=self.host,
                    port=self.port,
                    use_tls=self.use_tls,
                    timeout=self.timeout,
                )
                await self._session.connect()

                if self.username and self.password:
                    await self._session.login(self.username, self.password)

            self._reference_count += 1

    async def disconnect(self) -> None:
        async with self._lock:
            if self._reference_count > 0:
                self._reference_count -= 1

                if self._reference_count == 0 and self._session:
                    try:
                        await self._session.quit()
                    except Exception:
                        try:
                            await self._session.close()
                        except Exception:
                            pass
                    finally:
                        self._session = None

    def _create_message(
        self,
        from_addr: str,
        to_addrs: List[str],
        subject: str,
        body: str,
    ) -> MIMEMultipart:
        message = MIMEMultipart()

        message["From"] = from_addr
        message["To"] = ", ".join(to_addrs)
        message["Subject"] = subject

        if body:
            text_part = MIMEText(body, "plain", "utf-8")
            message.attach(text_part)

        return message

    async def send_notify(
        self,
        to_addrs: List[str],
        subject: str,
        notify: str,
    ) -> Dict[str, Any]:
        if not self._session:
            await self.connect()

        recipients = to_addrs.copy()

        message = self._create_message(
            from_addr=self.username,
            to_addrs=to_addrs,
            subject=subject,
            body=notify,
        )

        try:
            if not self._session:
                raise RuntimeError(
                    "EmailSender должен использоваться как контекстный менеджер"
                )
            await self._session.send_message(
                message, sender=self.username, recipients=recipients
            )

            return {
                "success": True,
                "message": "Email отправлен успешно",
                "error": None,
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Ошибка отправки email: {str(e)}",
                "error": e,
            }

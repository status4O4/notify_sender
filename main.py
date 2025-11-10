import re
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr, field_validator

from notify_manager.manager import get_notify_manager


scheduler = AsyncIOScheduler()
notify_manager = get_notify_manager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.start()
    notify_manager.initialize()
    yield
    scheduler.shutdown()


app = FastAPI(
    title="Notification Service",
    description="Простой сервис для уведомлений",
    version="1.0.0",
    lifespan=lifespan,
)


class NotificationRequest(BaseModel):
    phone: str
    email: EmailStr
    tg_id: str
    notification_date: datetime
    message: str = "Напоминание"

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v):
        phone_clean = re.sub(r"\D", "", v)
        if len(phone_clean) < 10:
            raise ValueError("Номер телефона должен содержать минимум 10 цифр")
        return phone_clean

    @field_validator("tg_id")
    @classmethod
    def validate_tg_id(cls, v):
        if not v.isdigit():
            raise ValueError("Telegram ID должен быть числом")
        return v


class NotificationResponse(BaseModel):
    status: str
    message: str
    notification_id: str
    scheduled_time: datetime


notifications_db = []
scheduled_jobs: Dict[str, str] = {}


async def send_notification(notification_id: str):
    notification = next(
        (n for n in notifications_db if n["id"] == notification_id), None
    )

    if not notification:
        return

    result = await notify_manager.send_notify(
        phone=notification.get("phone"),
        email=notification.get("email"),
        tg_id=notification.get("tg_id"),
        message=notification.get("message"),
    )

    print(result)

    task_status = "sent"
    if not result or result.get("error"):
        task_status = "error"

    notification["status"] = task_status
    notification["sent_at"] = datetime.now()

    job_id = scheduled_jobs.get(notification_id)
    if job_id:
        del scheduled_jobs[notification_id]


@app.post("/schedule-notification", response_model=NotificationResponse)
async def schedule_notification(request: NotificationRequest):
    if request.notification_date <= datetime.now():
        raise HTTPException(
            status_code=400, detail="Дата уведомления должна быть в будущем"
        )

    notification_id = str(uuid.uuid4())

    notification_data = {
        "id": notification_id,
        **request.model_dump(),
        "created_at": datetime.now(),
        "status": "scheduled",
    }

    notifications_db.append(notification_data)

    job = scheduler.add_job(
        send_notification,
        trigger=DateTrigger(run_date=request.notification_date),
        args=[notification_id],
        id=notification_id,
        misfire_grace_time=60,
    )

    scheduled_jobs[notification_id] = job.id

    return NotificationResponse(
        status="success",
        message="ok",
        notification_id=notification_id,
        scheduled_time=request.notification_date,
    )


@app.get("/notifications")
async def get_notifications():
    return {"total": len(notifications_db), "notifications": notifications_db}


@app.get("/")
async def root():
    return {
        "message": "Notification Service API",
        "endpoints": {
            "schedule_notification": "POST /schedule-notification",
            "get_notifications": "GET /notifications",
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

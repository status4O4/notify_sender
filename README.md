# notify_sender

REST API сервис для отправки уведомлений.

## Быстрый запуск

1. Установите зависимости:
```bash
pip install -r requirements.txt
```

2. Создайте `.env` файл:
```env
# Email (Yandex)
EMAIL_NOTIFIER_HOST=smtp.yandex.ru
EMAIL_NOTIFIER_PORT=587
EMAIL_NOTIFIER_LOGIN=your_email@yandex.ru
EMAIL_NOTIFIER_PASS=your_app_password

# SMS (SMSC.ru)
SMS_NOTIFIER_LOGIN=your_smsc_login
SMS_NOTIFIER_PASSWORD=your_smsc_password
SMS_NOTIFIER_SENDER=YourSenderName

# Telegram
TG_NOTIFIER_BOT_TOKEN=your_telegram_bot_token
```

3. Запустите сервер:
```bash
python main.py
```

API будет доступно на `http://localhost:8000`

## Используемые сервисы

- **Email**: Yandex Mail (ya.ru)
- **SMS**: SMSC.ru REST API  

## Примеры запросов

```bash
# Создать уведомление
curl -X POST http://localhost:8000/schedule-notification \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+7777777777777",
    "email": "asldkjfasda@test.ru",
    "tg_id": "123412341",
    "notification_date": "2025-12-10T22:02:00",
    "message": "Напоминание о встрече"
  }'
```

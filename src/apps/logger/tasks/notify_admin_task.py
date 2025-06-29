import time

from celery import shared_task

from ..send_bot_message import send_bot_message


@shared_task(bind=True)
def notifyAdminTask(self, message: str, _from: str = "API-Request"):
    time.sleep(1)
    formatted_message = f"<pre>📍{_from}\n{message}</pre>"
    res = send_bot_message(formatted_message)
    return f"{res.status_code}:{res.text}"

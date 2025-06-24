import logging
import time
from ..tasks.notify_admin_task import notifyAdminTask

class TelegramBotAlertHandler(logging.Handler):

    # def __init__(self, bot_token, chat_id):
    #     super().__init__()
    #     self.chat_id = chat_id

    def emit(self, record):
        log_entry = self.format(record)
        notifyAdminTask.delay(message=log_entry)

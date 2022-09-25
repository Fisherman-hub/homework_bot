import json
import logging
import project_utils

project_utils.logging_settings()


class BaseExceptions(Exception):
    """Базовая класс ошибки."""
    def __init__(self, message):
        self.message = message

    def __str__(self):
        logging.error(self.message)


class JSONDecodeError(BaseExceptions, json.JSONDecodeError):
    """Ошибка декодирования json файла."""

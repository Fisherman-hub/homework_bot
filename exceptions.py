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


class TelegramError(BaseExceptions):
    """Ошибка отправки сообщения."""


class WorkStatusNotChanged(BaseExceptions):
    """Ошибка статус работы не изменился."""


class WrongAPIResponseCodeError(BaseExceptions):
    """Ответ сервера отличен от 200."""


class ConnectionError(BaseExceptions):
    """Ошибка подключения."""


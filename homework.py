import logging
import os
import requests
import time
from http import HTTPStatus
import exceptions
import project_utils
import telegram
import sys
from typing import Dict

from dotenv import load_dotenv

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot: telegram.Bot, message: str) -> None:
    """Отправка сообщение ботом."""
    logging.info('Попытка отправки сообщения в телеграмм чат')
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except telegram.error.TelegramError as error:
        raise telegram.error.TelegramError(
            f'Ошибка отправки сообщения {error}'
        )
    else:
        logging.info('Сообщение отправлено в чат.')


def get_api_answer(current_timestamp: int):
    """Делаем запрос к эндпоинту API сервиса."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}

    request_params = {
        'url': ENDPOINT,
        'headers': HEADERS,
        'params': params
    }

    try:
        logging.info(
            (

                'Начинаем подключение к эндпоинту {url} с параметрами'
                ' headers = {headers}; params = {params}'
            ).format(**request_params)
        )

        response = requests.get(
            **request_params
        )
        if response.status_code != HTTPStatus.OK:
            raise exceptions.WrongAPIResponseCodeError(
                'Ответ сервера не является успешным:'
                f' request params = {request_params};'
                f' http_code = {response.status_code};'
                f' reason = {response.reason}; '
                f' content = {response.text}'
            )
        logging.info('Соединение с сервером установлено')
        return response.json()
    except Exception as error:
        raise exceptions.ConnectionError(
            (
                'Во время подключения к эндпоинту {url} произошла'
                ' непредвиденная ошибка {error}'
                ' headers = {HEADERS};'
                ' params = {params}'
            ).format(error=error,
                     **request_params)
        )


def check_response(response) -> list:
    """Проверка корректности полученного ответа."""
    if not isinstance(response, dict):
        raise TypeError('Аргумент функции не подходящего типа.')

    if not isinstance(response['homeworks'], list):
        raise TypeError('Аргумент функции не подходящего типа.')

    homeworks = response.get('homeworks')
    if 'homeworks' in homeworks or 'current_date' in homeworks:
        raise KeyError(
            'Ключи homeworks или current_date отсутствуют в переменной.'
        )

    if homeworks is None:
        raise TypeError(f'Переменная имеет значение - {homeworks}')
    return homeworks


def parse_status(homework) -> str:
    """Проверка статуса домашней работы."""
    homework_name = homework['homework_name']
    homework_status = homework['status']

    if homework_status not in HOMEWORK_STATUSES:
        raise KeyError('Недокументированный статус домашней работы')

    if homework_name and homework_status in HOMEWORK_STATUSES:
        verdict = HOMEWORK_STATUSES[homework_status]
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'

    else:
        raise exceptions.WorkStatusNotChanged('Статус работы не изменился.')


def check_tokens() -> bool:
    """Проверка возможности получения токенов."""
    check_params = (PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)
    if all(check_params):
        logging.info('Токены получены.')
        return True
    else:
        logging.error('Токены не получены.')
        return False


def main() -> None:
    """Основная логика работы бота."""
    if not check_tokens():
        message = (
            'Отсутствуют обязательные переменные окружения:'
            ' PRACTICUM_TOKEN,'
            ' TELEGRAM_TOKEN, '
            ' TELEGRAM_CHAT_ID.'
            ' Программа принудительно остановлена.'
        )
        logging.critical(message)
        sys.exit(message)

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())

    while True:
        try:
            current_report: Dict = {
                'name': '',
                'output': ''
            }
            prev_report: Dict = current_report.copy()

            response = get_api_answer(current_timestamp)

            current_timestamp = response.get('current_date', current_timestamp)
            new_homeworks = check_response(response)

            if new_homeworks:
                current_report['name'] = new_homeworks[0]['homework_name']
                current_report['output'] = parse_status(new_homeworks[0])
            else:
                current_report['output'] = (
                    f'За период от {current_timestamp} до настоящего момента'
                    ' домашних работ нет.'
                )

            if current_report != prev_report:
                send_message(bot, current_report)
                prev_report = current_report.copy()

            else:
                logging.debug('В ответе нет новых статусов.')

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            current_report['output'] = message
            logging.error(message, exc_info=True)
            if current_report != prev_report:
                send_message(bot, current_report)
                prev_report = current_report.copy()

        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    project_utils.logging_settings()
    main()

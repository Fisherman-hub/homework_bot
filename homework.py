import logging
import os
import requests
import time
from http import HTTPStatus
import exceptions
import project_utils
import telegram

from dotenv import load_dotenv

load_dotenv()
project_utils.logging_settings()

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
    bot.send_message(TELEGRAM_CHAT_ID, message)


def get_api_answer(current_timestamp: int):
    """Делаем запрос к эндпоинту API сервиса."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}

    api_params = {
        'url': ENDPOINT,
        'headers': HEADERS,
        'params': params
    }

    logging.info('Начали запрос к API')
    try:
        response = requests.get(
            url=api_params['url'],
            headers=api_params['headers'],
            params=api_params['params']
        )
        if response.status_code != HTTPStatus.OK:
            message = f'Код ответа сервера {response.status_code}'
            raise requests.exceptions.HTTPError(message)
        logging.info('Соединение с сервером установлено')
        return response.json()
    except exceptions.JSONDecodeError:
        raise exceptions.JSONDecodeError(
            'json файл не поддается декодированию'
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

    if homework_name and homework_status:
        verdict = HOMEWORK_STATUSES[homework_status]
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'

    else:
        return None


def check_tokens() -> bool:
    """Проверка возможности получения токенов."""
    if PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        logging.info('Токены получены.')
        return True
    else:
        logging.error('Токены не получены.')
        return False


def main() -> None:
    """Основная логика работы бота."""
    if check_tokens():
        bot = telegram.Bot(token=TELEGRAM_TOKEN)
        current_timestamp = int(time.time())

        logging.info('Создан экземпляр класса Bot')

        while True:
            try:
                response = get_api_answer(current_timestamp)
                homeworks = check_response(response)
                answer = parse_status(homeworks)
                if answer is not None:
                    send_message(bot, answer)

                current_timestamp = int(time.time())
                time.sleep(RETRY_TIME)

            except Exception as error:
                message = f'Сбой в работе программы: {error}'
                send_message(bot, message)
                time.sleep(RETRY_TIME)
            else:
                logging.info('Цикл  функции main выполнился без ошибок')
    else:
        time.sleep(RETRY_TIME)
        main()


if __name__ == '__main__':
    main()

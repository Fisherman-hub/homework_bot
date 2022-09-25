import logging


def logging_settings():
    logging.basicConfig(
        level=logging.INFO,
        filename='main.log',
        filemode='w',
        format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'
    )

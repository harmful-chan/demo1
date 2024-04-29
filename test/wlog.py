import logging
import os


def setup_logging(log_file, mode='a', print_=True):
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    logger = logging.getLogger(log_file)
    logger.setLevel(logging.DEBUG)

    file_handler = logging.FileHandler(log_file, mode=mode, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M')
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)

    if print_:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger




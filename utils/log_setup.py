import logging


def setup_logger(log_level=logging.INFO, name='TO'):
    logger = logging.getLogger(name)
    if not logger.handlers:
        # Set the log level
        logger.setLevel(log_level)
        # Create a console handler and set level to debug
        ch = logging.StreamHandler()
        ch.setLevel(log_level)
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        # Add formatter to ch
        ch.setFormatter(formatter)
        # Add ch to logger
        logger.addHandler(ch)
    return logger

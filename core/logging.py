import logging
import sys

# ANSI color codes
class LogColor:
    RESET = "\033[0m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    CYAN = "\033[36m"
    BOLD = "\033[1m"


class ColorFormatter(logging.Formatter):
    COLORS = {
        logging.DEBUG: LogColor.CYAN,
        logging.INFO: LogColor.GREEN,
        logging.WARNING: LogColor.YELLOW,
        logging.ERROR: LogColor.RED,
        logging.CRITICAL: LogColor.BOLD + LogColor.RED,
    }

    def format(self, record):
        color = self.COLORS.get(record.levelno, LogColor.RESET)

        record.levelname = f"{color}{record.levelname}{LogColor.RESET}"
        record.msg = f"{color}{record.msg}{LogColor.RESET}"

        return super().format(record)


def setup_logger(name="app"):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # prevent duplicate handlers (important di FastAPI reload)
    if logger.handlers:
        return logger

    handler = logging.StreamHandler(sys.stdout)

    formatter = ColorFormatter(
        "%(levelname)s:\t "
        " %(message)s",
        datefmt="%H:%M:%S",
    )

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger
import logging
import sys
import os
from logging.handlers import RotatingFileHandler
from logging import StreamHandler, FileHandler
from colorama import Fore, Style, init as colorama_init

colorama_init(autoreset=True)


class ColoredFormatter(logging.Formatter):
    COLORS = {
        logging.DEBUG: Fore.BLUE,
        logging.INFO: Fore.GREEN,
        logging.WARNING: Fore.YELLOW,
        logging.ERROR: Fore.RED,
        logging.CRITICAL: Fore.MAGENTA + Style.BRIGHT,
    }

    def format(self, record):
        level_color = self.COLORS.get(record.levelno, "")
        reset = Style.RESET_ALL

        # Сохраняем оригинальные значения
        original_levelname = record.levelname
        original_msg = record.getMessage()

        # Красим только для консоли
        record.levelname = f"{level_color}{original_levelname}{reset}"
        record.msg = f"{level_color}{original_msg}{reset}"

        formatted = super().format(record)

        # Возвращаем оригинал, чтобы file_handler получил чистый текст
        record.levelname = original_levelname
        record.msg = original_msg

        return formatted


# Формат логов
FORMAT = "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
DATE_FORMAT = "%d.%m.%Y %H:%M:%S"

# Настраиваем логгер
logger = logging.getLogger("bot")
logger.setLevel(logging.DEBUG)

# Консольный хендлер (с цветами)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(ColoredFormatter(FORMAT, DATE_FORMAT))

# Файловый хендлер с ротацией (без цветов)
file_handler = RotatingFileHandler(
    "logs/bot.log", maxBytes=1_000_000, backupCount=5, encoding="utf-8"
)
file_handler.setFormatter(logging.Formatter(FORMAT, DATE_FORMAT))

# Добавляем оба хендлера
logger.addHandler(console_handler)
logger.addHandler(file_handler)

def disable_console(logger_name="bot"):
    """Отключает только консольный вывод, не трогая файл."""
    log = logging.getLogger(logger_name)
    for h in log.handlers[:]:
        if isinstance(h, StreamHandler) and not isinstance(h, FileHandler):
            log.removeHandler(h)

def set_logger(path: str, to_console=True) -> logging.Logger:
    """
    Создаёт новый логгер с именем по имени файла.
    Пример: set_log_file("logs/server.log") → логгер 'server'
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)

    # имя логгера = имя файла без расширения
    name = os.path.splitext(os.path.basename(path))[0]
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # избегаем дублирования хендлеров
    if logger.handlers:
        return logger

    # файл
    file_handler = RotatingFileHandler(
        path, maxBytes=1_000_000, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(logging.Formatter(FORMAT, DATE_FORMAT))
    logger.addHandler(file_handler)

    # консоль (по желанию)
    if to_console:
        console_handler = StreamHandler(sys.stdout)
        console_handler.setFormatter(ColoredFormatter(FORMAT, DATE_FORMAT))
        logger.addHandler(console_handler)

    return logger

import logging
import os

def setup_logger():
    logger = logging.getLogger("app")
    level = logging.DEBUG if os.getenv("ENV") == "dev" else logging.INFO
    logger.setLevel(level)

    # Evita duplicação de logs
    if logger.hasHandlers():
        return logger

    # 📄 Formato do log
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    # 🖥️ Console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)

    # 📁 Arquivo
    file_handler = logging.FileHandler("app.log", encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    # Adiciona os handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger
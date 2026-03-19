import logging
import sys

from loguru import logger as loguru_logger

from app.config import get_settings

settings = get_settings()
loguru_logger.configure(extra={"request_id": "-"})
logger = loguru_logger.patch(lambda record: record["extra"].setdefault("request_id", "-"))


class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def setup_logging() -> None:
    loguru_logger.configure(extra={"request_id": "-"})
    logging.root.handlers = [InterceptHandler()]
    logging.root.setLevel(settings.LOG_LEVEL)

    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"):
        logging_logger = logging.getLogger(logger_name)
        logging_logger.handlers = [InterceptHandler()]
        logging_logger.propagate = False

    logger.remove()
    logger.add(
        sys.stdout,
        level=settings.LOG_LEVEL,
        backtrace=settings.DEBUG,
        diagnose=settings.DEBUG,
        enqueue=True,
        serialize=False,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "{extra[request_id]} | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
    )


logger = logger.bind(request_id="-")

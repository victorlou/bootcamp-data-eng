import sys
from logging import Logger
from logging.config import dictConfig
from os import getenv
from traceback import format_exception
from types import TracebackType
from typing import Dict, Optional, Type

import structlog
from dotenv import load_dotenv


def configure_local_logging(level: str = "DEBUG") -> None:
    timestamper = structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S")
    pre_chain = [
        structlog.stdlib.add_log_level,
        timestamper,
    ]

    handlers_config: Dict[str, object] = {
        "default": {
            "level": level,
            "class": "logging.StreamHandler",
            "formatter": "colored",
        },
        # "file": {
        #     "level": level,
        #     "class": "logging.handlers.WatchedFileHandler",
        #     "filename": __name__ + ".log",
        #     "formatter": "plain",
        # },
    }

    if getenv("LOGGER_LOKI_ACTIVATE", "FALSE").upper() == "TRUE":
        handlers_config["loki"] = {
            "level": level,
            "class": "logging_loki.LokiHandler",
            "formatter": "colored",
            "url": getenv("LOGGER_LOKI_URL"),
            "tags": {
                "company": getenv("ERATHOS_COMPANY"),
                "project": getenv("ERATHOS_PROJECT"),
                "environment": getenv("ERATHOS_ENVIRONMENT", "development"),
            },
            "auth": (
                getenv("LOGGER_LOKI_USER"),
                getenv("LOGGER_LOKI_PASSWORD"),
            ),
            "version": "1",
        }

    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": True,
            "formatters": {
                "plain": {
                    "()": structlog.stdlib.ProcessorFormatter,
                    "processor": structlog.dev.ConsoleRenderer(colors=False),
                    "foreign_pre_chain": pre_chain,
                },
                "colored": {
                    "()": structlog.stdlib.ProcessorFormatter,
                    "processor": structlog.dev.ConsoleRenderer(colors=True),
                    "foreign_pre_chain": pre_chain,
                },
            },
            "handlers": handlers_config,
            "loggers": {
                "": {
                    "handlers": list(handlers_config.keys()),
                    "level": level,
                    "propagate": True,
                },
            },
        }
    )

    structlog.configure_once(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            timestamper,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger() -> Logger:
    if not structlog.is_configured():
        init_logger()
    return structlog.get_logger("structlog-logger")


def handle_uncaught_exception(
    type: Optional[Type[BaseException]],
    value: BaseException,
    traceback_object: TracebackType,
) -> None:
    logger = get_logger()
    details = (
        f"{type.__dict__['__doc__']}\n"
        if type and hasattr(type, "__dict__") and type.__dict__.get("__doc__")
        else ""
    )
    error = details + "".join(format_exception(type, value, traceback_object))
    logger.critical("uncaught-exception", error=error)


def init_logger() -> None:
    load_dotenv()
    configure_local_logging(getenv("LOGGER_LEVEL", "DEBUG"))
    sys.excepthook = handle_uncaught_exception  # type: ignore

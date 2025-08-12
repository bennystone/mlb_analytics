import logging
import os

import structlog


def configure_logging() -> None:
    logging.basicConfig(
        format="%(message)s",
        stream=os.sys.stdout,
        level=os.getenv("LOG_LEVEL", "INFO"),
    )
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
    )

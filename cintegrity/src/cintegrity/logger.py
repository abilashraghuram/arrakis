from __future__ import annotations

import json
import logging
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

LOGGER_NAME = "cintegrity"
DEFAULT_LOG_DIR = "logs"
DEFAULT_LOG_FILE = "gateway.log"


@dataclass(frozen=True)
class LoggingConfig:
    level: int = logging.INFO
    file: str | None = None
    enable_file_logging: bool = True
    log_dir: str = DEFAULT_LOG_DIR
    log_rotation: bool = False
    max_bytes: int = 10 * 1024 * 1024
    backup_count: int = 5


class DetailedTextFormatter(logging.Formatter):
    """Formatter for human-readable file logs with detailed information."""

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        module = record.name.split(".")[-1] if "." in record.name else record.name
        base_line = f"{timestamp} | {record.levelname:5s} | {module:20s} | {record.getMessage()}"
        lines = [base_line]

        for key, value in record.__dict__.items():
            if key in {
                "args",
                "asctime",
                "created",
                "exc_info",
                "exc_text",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "msg",
                "name",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "stack_info",
                "thread",
                "threadName",
                "message",
            }:
                continue
            if key.startswith("_"):
                continue

            if isinstance(value, dict):
                lines.append(f"  {key.title()}: {json.dumps(value, indent=2)}")
            elif isinstance(value, (list, tuple)):
                lines.append(f"  {key.title()}: {json.dumps(value, indent=2)}")
            elif isinstance(value, str) and len(value) > 100:
                lines.append(f"  {key.title()}: {value[:100]}...")
            else:
                lines.append(f"  {key.title()}: {value}")

        if record.exc_info:
            lines.append("  Traceback:")
            import traceback

            lines.append("    " + "\n    ".join(traceback.format_exception(*record.exc_info)))

        lines.append("")
        return "\n".join(lines)


def get_logger(name: str | None = None) -> logging.Logger:
    logger = logging.getLogger(name or LOGGER_NAME)
    if not any(isinstance(h, logging.NullHandler) for h in logger.handlers):
        logger.addHandler(logging.NullHandler())
    return logger


def configure_logging(config: LoggingConfig | None = None) -> None:
    config = config or LoggingConfig()
    logger = logging.getLogger(LOGGER_NAME)
    logger.handlers.clear()
    logger.setLevel(config.level)
    logger.propagate = False

    # Add file handler if enabled
    if config.enable_file_logging and not config.file:
        log_dir = Path(config.log_dir)
        log_file = log_dir / DEFAULT_LOG_FILE
        try:
            log_dir.mkdir(parents=True, exist_ok=True)

            if config.log_rotation:
                from logging.handlers import RotatingFileHandler

                file_handler: logging.Handler = RotatingFileHandler(
                    log_file,
                    mode="a",
                    maxBytes=config.max_bytes,
                    backupCount=config.backup_count,
                )
            else:
                file_handler = logging.FileHandler(log_file, mode="a")

            file_handler.setLevel(config.level)
            file_handler.setFormatter(DetailedTextFormatter())
            logger.addHandler(file_handler)
        except (OSError, PermissionError) as e:
            sys.stderr.write(f"Warning: Could not create log file {log_file}: {e}\n")
            sys.stderr.write("Falling back to stdout/stderr logging only\n")

    # Use custom FileHandler if file is specified, otherwise StreamHandler to stderr
    if config.file:
        main_handler = logging.FileHandler(config.file, mode="w")
        main_handler.setLevel(config.level)
        main_handler.setFormatter(logging.Formatter("[%(levelname)s] %(name)s: %(message)s"))
        logger.addHandler(main_handler)
    else:
        # Output to stderr by default
        main_handler = logging.StreamHandler(sys.stderr)
        main_handler.setLevel(config.level)
        main_handler.setFormatter(logging.Formatter("[%(levelname)s] %(name)s: %(message)s"))
        logger.addHandler(main_handler)

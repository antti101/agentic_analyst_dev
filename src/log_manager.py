import logging
import json
import os

class JsonFormatter(logging.Formatter):
    """Formats log records as single-line JSON, including extra custom fields."""

    def format(self, record):
        # Core standard fields in LogRecord
        standard_fields = {
            'args', 'asctime', 'created', 'exc_info', 'exc_text', 'filename',
            'funcName', 'levelname', 'levelno', 'lineno', 'module',
            'msecs', 'message', 'msg', 'name', 'pathname', 'process',
            'processName', 'relativeCreated', 'stack_info', 'thread', 'threadName'
        }

        log_object = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add custom extra fields if any
        for key, value in record.__dict__.items():
            if key not in standard_fields:
                log_object[key] = value

        return json.dumps(log_object, ensure_ascii=False)

def get_json_logger(name="agent_logger", log_file=None):
    """Creates a logger that writes structured JSON logs to a .jsonl file."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        # Default log path inside assets/logs if not specified
        if not log_file:
            os.makedirs("assets/logs", exist_ok=True)
            log_file = os.path.join("assets/logs", f"{name}.jsonl")

        handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)

        # Optional: also stream to console in plain text for debugging
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        logger.addHandler(console_handler)

        logger.info(f"JSON logger initialized at {log_file}")

    return logger

# Global logger instance
logger = get_json_logger()

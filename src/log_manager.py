import logging
import json

class JsonFormatter(logging.Formatter):
    """Formats log records as a single-line JSON object, including extra fields."""
    def format(self, record):
        # These are the standard attributes of a LogRecord
        standard_fields = {
            'args', 'asctime', 'created', 'exc_info', 'exc_text', 'filename', 
            'funcName', 'levelname', 'levelno', 'lineno', 'module', 
            'msecs', 'message', 'msg', 'name', 'pathname', 'process', 
            'processName', 'relativeCreated', 'stack_info', 'thread', 'threadName'
        }
        
        # Start with the standard fields we want
        log_object = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
        }

        # Add any extra fields passed to the logger
        for key, value in record.__dict__.items():
            if key not in standard_fields:
                log_object[key] = value
                
        return json.dumps(log_object)

def get_json_logger(name="agent_logger", log_file="agent_logs.jsonl"):
    """Sets up and returns a logger that writes to a JSONL file."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        handler = logging.FileHandler(log_file, mode='w')
        formatter = JsonFormatter()
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
    return logger

# Global logger instance
logger = get_json_logger()
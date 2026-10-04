import logging
import json
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


class StructuredFormatter(logging.Formatter):
    """
    JSON structured log formatter for machine readability and structured analysis.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_obj: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Include extra attributes if provided (structured logging event payload)
        if hasattr(record, "event"):
            log_obj["event"] = record.event
        if hasattr(record, "data") and isinstance(record.data, dict):
            log_obj["data"] = record.data
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_obj, ensure_ascii=False)


def setup_logging(level: str = "INFO", json_logs: bool = False) -> logging.Logger:
    """
    Configure root application logging.
    """
    logger = logging.getLogger("tiktok_trend_hunter")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # Avoid duplicate handlers
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        if json_logs:
            handler.setFormatter(StructuredFormatter())
        else:
            handler.setFormatter(
                logging.Formatter(
                    "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S"
                )
            )
        logger.addHandler(handler)
        
    return logger


logger = setup_logging()


def log_event(event_name: str, message: str, data: Optional[Dict[str, Any]] = None, level: int = logging.INFO) -> None:
    """
    Helper for emitting structured log events without leaking sensitive credentials or raw HTML.
    """
    extra = {"event": event_name, "data": data or {}}
    logger.log(level, f"[{event_name}] {message}", extra=extra)

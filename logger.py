import logging
import json
import os
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "layer": getattr(record, "layer", "app"),
            "event": getattr(record, "event", record.getMessage()),
            "data": getattr(record, "data", {}),
        })


class BannerFormatter(logging.Formatter):
    def format(self, record):
        layer = getattr(record, "layer", "app")
        return f"  [{layer}] {record.getMessage()}"


class RequestLogger:
    def __init__(self, conversation_id, message: str):
        self.conversation_id = conversation_id
        self.start_time = datetime.now(timezone.utc)

        os.makedirs("logs", exist_ok=True)
        timestamp = self.start_time.strftime("%Y%m%d-%H%M%S")
        conv_label = str(conversation_id) if conversation_id is not None else "no-conv"
        self.log_file = f"logs/{conv_label}-{timestamp}.log"

        self._logger = logging.getLogger(f"request.{conv_label}.{timestamp}")
        self._logger.setLevel(logging.DEBUG)
        self._logger.propagate = False

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(BannerFormatter())

        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(JsonFormatter())

        self._logger.addHandler(console_handler)
        self._logger.addHandler(file_handler)

        self._print_banner(f"REQUEST  conversationId={conv_label}  msg=\"{message[:80]}\"")

    def _print_banner(self, text: str):
        line = "═" * 48
        print(f"\n{line}")
        print(f" {text}")
        print(f"{line}")

    def section(self, title: str):
        print(f"\n=== {title} ===")

    def debug(self, msg: str, layer: str = "app", event: str = "", data: dict = None):
        self._logger.debug(msg, extra={"layer": layer, "event": event or msg, "data": data or {}})

    def info(self, msg: str, layer: str = "app", event: str = "", data: dict = None):
        self._logger.info(msg, extra={"layer": layer, "event": event or msg, "data": data or {}})

    def error(self, msg: str, layer: str = "app", event: str = "", data: dict = None):
        self._logger.error(msg, extra={"layer": layer, "event": event or msg, "data": data or {}})

    def close(self, error: bool = False):
        elapsed = (datetime.now(timezone.utc) - self.start_time).total_seconds()
        status = "REQUEST ERROR" if error else "REQUEST COMPLETE"
        self._print_banner(f"{status}  duration={elapsed:.2f}s")
        for handler in self._logger.handlers[:]:
            handler.close()
            self._logger.removeHandler(handler)

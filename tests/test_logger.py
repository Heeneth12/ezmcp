import json
import pytest
from unittest.mock import patch
from logger import RequestLogger


def test_request_logger_creates_log_file():
    with patch("logger.os.makedirs") as mock_mkdir, \
         patch("logger.logging.FileHandler") as mock_fh, \
         patch("logger.logging.StreamHandler"), \
         patch("logger.print"):
        mock_fh.return_value.level = 0
        mock_fh.return_value.setFormatter = lambda x: None
        logger = RequestLogger(42, "show me items")
        mock_mkdir.assert_called_once_with("logs", exist_ok=True)
        assert "42" in logger.log_file
        logger.close()


def test_request_logger_no_conversation_id():
    with patch("logger.os.makedirs"), \
         patch("logger.logging.FileHandler"), \
         patch("logger.logging.StreamHandler"), \
         patch("logger.print"):
        logger = RequestLogger(None, "hello")
        assert "no-conv" in logger.log_file
        logger.close()


def test_request_logger_debug_calls_underlying_logger():
    with patch("logger.os.makedirs"), \
         patch("logger.logging.FileHandler"), \
         patch("logger.logging.StreamHandler"):
        logger = RequestLogger(1, "test")

    with patch.object(logger._logger, "debug") as mock_debug:
        logger.debug("test message", layer="main", event="test_event", data={"k": "v"})
        mock_debug.assert_called_once()
        call_kwargs = mock_debug.call_args
        assert call_kwargs[1]["extra"]["layer"] == "main"
        assert call_kwargs[1]["extra"]["event"] == "test_event"
        assert call_kwargs[1]["extra"]["data"] == {"k": "v"}
    logger.close()


def test_request_logger_error_calls_underlying_logger():
    with patch("logger.os.makedirs"), \
         patch("logger.logging.FileHandler"), \
         patch("logger.logging.StreamHandler"):
        logger = RequestLogger(1, "test")

    with patch.object(logger._logger, "error") as mock_error:
        logger.error("boom", layer="main", event="err", data={"error": "oops"})
        mock_error.assert_called_once()
    logger.close()


def test_json_formatter_produces_valid_json():
    import logging
    from logger import JsonFormatter
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="test", level=logging.DEBUG,
        pathname="", lineno=0, msg="hello",
        args=(), exc_info=None
    )
    record.layer = "http"
    record.event = "http_request"
    record.data = {"url": "http://example.com"}
    output = formatter.format(record)
    parsed = json.loads(output)
    assert parsed["layer"] == "http"
    assert parsed["event"] == "http_request"
    assert parsed["data"] == {"url": "http://example.com"}
    assert "ts" in parsed
    assert "level" in parsed


def test_banner_formatter_includes_layer_and_message():
    import logging
    from logger import BannerFormatter
    formatter = BannerFormatter()
    record = logging.LogRecord(
        name="test", level=logging.DEBUG,
        pathname="", lineno=0, msg="fetching items",
        args=(), exc_info=None
    )
    record.layer = "main"
    output = formatter.format(record)
    assert "[main]" in output
    assert "fetching items" in output

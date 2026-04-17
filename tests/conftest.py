import pytest
from unittest.mock import MagicMock


@pytest.fixture
def mock_logger():
    logger = MagicMock()
    logger.debug = MagicMock()
    logger.info = MagicMock()
    logger.error = MagicMock()
    logger.section = MagicMock()
    logger.close = MagicMock()
    return logger

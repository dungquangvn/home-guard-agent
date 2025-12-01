import os
import sys
import tempfile
from pathlib import Path

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from modules.logging.logger import Logger


def test_logger_creates_log_directory(tmp_path):
    """Black-box: Logger creates log directory if missing"""
    log_file = tmp_path / "logs" / "system.log"
    logger = Logger(log_file=str(log_file))
    assert log_file.parent.exists()


def test_logger_info_writes_to_file(tmp_path):
    """Black-box: Logger.info() writes formatted message to file"""
    log_file = tmp_path / "system.log"
    logger = Logger(log_file=str(log_file))
    
    logger.info("Test info message")
    
    assert log_file.exists()
    content = log_file.read_text()
    assert "Test info message" in content
    assert "[INFO]" in content


def test_logger_warning_writes_to_file(tmp_path):
    """Black-box: Logger.warning() writes warning level message"""
    log_file = tmp_path / "system.log"
    logger = Logger(log_file=str(log_file))
    
    logger.warning("Test warning")
    
    content = log_file.read_text()
    assert "Test warning" in content
    assert "[WARNING]" in content


def test_logger_error_writes_to_file(tmp_path):
    """Black-box: Logger.error() writes error level message"""
    log_file = tmp_path / "system.log"
    logger = Logger(log_file=str(log_file))
    
    logger.error("Test error")
    
    content = log_file.read_text()
    assert "Test error" in content
    assert "[ERROR]" in content


def test_logger_debug_writes_to_file(tmp_path):
    """Black-box: Logger.debug() writes debug level message"""
    log_file = tmp_path / "system.log"
    logger = Logger(log_file=str(log_file))
    
    logger.debug("Test debug")
    
    content = log_file.read_text()
    assert "Test debug" in content
    assert "[DEBUG]" in content


def test_logger_multiple_messages_appended(tmp_path):
    """Black-box: Logger appends multiple messages to same file"""
    log_file = tmp_path / "system.log"
    logger = Logger(log_file=str(log_file))
    
    logger.info("First message")
    logger.error("Second message")
    logger.warning("Third message")
    
    content = log_file.read_text()
    assert "First message" in content
    assert "Second message" in content
    assert "Third message" in content
    
    # Should have 3 lines
    lines = content.strip().split("\n")
    assert len(lines) >= 3


def test_logger_includes_timestamp(tmp_path):
    """Black-box: Logger includes timestamp in each message"""
    log_file = tmp_path / "system.log"
    logger = Logger(log_file=str(log_file))
    
    logger.info("Timestamp test")
    
    content = log_file.read_text()
    # Check for YYYY-MM-DD HH:MM:SS pattern
    import re
    assert re.search(r'\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\]', content)


def test_logger_with_auto_flush_disabled(tmp_path):
    """Black-box: Logger respects auto_flush setting"""
    log_file = tmp_path / "system.log"
    logger = Logger(log_file=str(log_file), auto_flush=False)
    
    logger.info("Test without auto flush")
    
    # File should still contain message (flush happens on close)
    content = log_file.read_text()
    assert "Test without auto flush" in content

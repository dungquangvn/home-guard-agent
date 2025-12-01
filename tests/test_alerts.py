import os
import sys
import asyncio
import tempfile
import numpy as np
import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from modules.alerts.alerts import AlertService


def test_alert_service_creates_log_directory(tmp_path):
    """Black-box: AlertService creates log directory if missing"""
    log_file = tmp_path / "alerts" / "alert.log"
    config = {
        "log_file_path": str(log_file),
        "audio_path": "nonexistent.wav",
        "sender_email": "",
        "sender_password": "",
        "receiver_email": ""
    }
    
    service = AlertService(config)
    assert log_file.parent.exists()


def test_alert_service_write_to_file_sync(tmp_path):
    """Black-box: AlertService writes alert data to log file"""
    log_file = tmp_path / "alerts.txt"
    config = {
        "log_file_path": str(log_file),
        "audio_path": "nonexistent.wav",
        "sender_email": "",
        "sender_password": "",
        "receiver_email": ""
    }
    
    service = AlertService(config)
    frame = np.zeros((24, 32, 3), dtype=np.uint8)
    alert_data = {
        "track_id": 123,
        "label": "TestPerson",
        "message": "Test alert message",
        "frame": frame
    }
    
    # Call sync method directly
    service._write_to_file_sync(alert_data)
    
    # Verify file was written and contains expected content
    assert log_file.exists()
    content = log_file.read_text()
    assert "123" in content  # track_id
    assert "TestPerson" in content  # label
    assert "Test alert message" in content  # message


def test_alert_service_play_sound_sync_no_audio(tmp_path):
    """Black-box: AlertService handles missing audio gracefully"""
    log_file = tmp_path / "alerts.txt"
    config = {
        "log_file_path": str(log_file),
        "audio_path": str(tmp_path / "nonexistent.wav"),
        "sender_email": "",
        "sender_password": "",
        "receiver_email": ""
    }
    
    service = AlertService(config)
    
    # Call should not raise exception
    service._play_sound_sync()


def test_alert_service_send_email_sync_no_credentials(tmp_path):
    """Black-box: AlertService skips email when credentials missing"""
    log_file = tmp_path / "alerts.txt"
    config = {
        "log_file_path": str(log_file),
        "audio_path": "nonexistent.wav",
        "sender_email": "",
        "sender_password": "",
        "receiver_email": ""
    }
    
    service = AlertService(config)
    frame = np.zeros((24, 32, 3), dtype=np.uint8)
    alert_data = {
        "track_id": 456,
        "label": "TestObj",
        "message": "test",
        "frame": frame
    }
    
    # Should not raise exception when credentials missing
    service._send_email_sync(alert_data, frame)


@pytest.mark.asyncio
async def test_alert_service_on_alert_requested_async(tmp_path):
    """Black-box: AlertService.on_alert_requested processes alert data asynchronously"""
    log_file = tmp_path / "alerts.txt"
    config = {
        "log_file_path": str(log_file),
        "audio_path": "nonexistent.wav",
        "sender_email": "",
        "sender_password": "",
        "receiver_email": ""
    }
    
    service = AlertService(config)
    frame = np.zeros((24, 32, 3), dtype=np.uint8)
    alert_data = {
        "track_id": 789,
        "label": "AsyncTest",
        "message": "async alert",
        "frame": frame
    }
    
    # Call async handler
    await service.on_alert_requested(alert_data)
    
    # Verify file was written
    assert log_file.exists()
    content = log_file.read_text()
    assert "789" in content
    assert "AsyncTest" in content

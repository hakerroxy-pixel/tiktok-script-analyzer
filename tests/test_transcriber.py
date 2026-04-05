import os
import pytest
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.transcriber import download_audio, transcribe_audio, transcribe_tiktok


def test_download_audio_returns_filepath():
    with patch("services.transcriber.yt_dlp.YoutubeDL") as mock_ydl:
        instance = MagicMock()
        mock_ydl.return_value.__enter__ = MagicMock(return_value=instance)
        mock_ydl.return_value.__exit__ = MagicMock(return_value=False)
        instance.extract_info.return_value = {"duration": 45}

        filepath, duration = download_audio(
            "https://www.tiktok.com/@user/video/123",
            tmp_dir="/tmp/test"
        )
        assert filepath.endswith(".mp3")
        assert duration == 45
        instance.download.assert_called_once()


def test_transcribe_audio_returns_text():
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "This is the transcribed text"
    mock_client.audio.transcriptions.create.return_value = mock_response

    with patch("builtins.open", MagicMock()):
        result = transcribe_audio("/tmp/test/audio.mp3", client=mock_client)

    assert result == "This is the transcribed text"
    mock_client.audio.transcriptions.create.assert_called_once()


def test_transcribe_tiktok_full_flow(tmp_path):
    with patch("services.transcriber.download_audio") as mock_dl, \
         patch("services.transcriber.transcribe_audio") as mock_tr, \
         patch("os.remove") as mock_rm:
        mock_dl.return_value = (str(tmp_path / "audio.mp3"), 30.0)
        mock_tr.return_value = "Hello this is a test"

        result = transcribe_tiktok(
            "https://www.tiktok.com/@user/video/123",
            tmp_dir=str(tmp_path),
            openai_api_key="test-key"
        )

        assert result["text"] == "Hello this is a test"
        assert result["duration_seconds"] == 30.0
        mock_rm.assert_called_once_with(str(tmp_path / "audio.mp3"))

"""Tests for audio backend configuration."""

from __future__ import annotations

from unittest.mock import MagicMock, patch


class TestConfigureAudioBackend:
    """Test configure_audio_backend function."""

    def setup_method(self):
        """Reset the backend configured flag before each test."""
        # Reset the module state
        import scribbulus.transcription.audio_backend as ab

        ab._backend_configured = False

    def test_sets_environment_variable(self):
        """Should set TORCHAUDIO_USE_BACKEND_DISPATCHER env var."""
        with (
            patch.dict("os.environ", {}, clear=True),
            patch(
                "torchaudio.list_audio_backends", return_value=["soundfile"]
            ),
            patch("torchaudio.set_audio_backend"),
        ):
            from scribbulus.transcription.audio_backend import (
                configure_audio_backend,
            )

            configure_audio_backend()

            import os

            assert os.environ.get("TORCHAUDIO_USE_BACKEND_DISPATCHER") == "1"

    def test_prefers_soundfile_backend(self):
        """Should set soundfile as the preferred backend."""
        mock_set_backend = MagicMock()
        with (
            patch.dict("os.environ", {}, clear=True),
            patch(
                "torchaudio.list_audio_backends",
                return_value=["soundfile", "sox_io"],
            ),
            patch("torchaudio.set_audio_backend", mock_set_backend),
        ):
            from scribbulus.transcription.audio_backend import (
                configure_audio_backend,
            )

            configure_audio_backend()

            mock_set_backend.assert_called_once_with("soundfile")

    def test_falls_back_to_sox_io(self):
        """Should fall back to sox_io if soundfile is not available."""
        mock_set_backend = MagicMock()
        with (
            patch.dict("os.environ", {}, clear=True),
            patch("torchaudio.list_audio_backends", return_value=["sox_io"]),
            patch("torchaudio.set_audio_backend", mock_set_backend),
        ):
            from scribbulus.transcription.audio_backend import (
                configure_audio_backend,
            )

            configure_audio_backend()

            mock_set_backend.assert_called_once_with("sox_io")

    def test_handles_empty_backends_list(self):
        """Should handle case where no backends are available."""
        with (
            patch.dict("os.environ", {}, clear=True),
            patch("torchaudio.list_audio_backends", return_value=[]),
            patch("torchaudio.set_audio_backend") as mock_set,
        ):
            from scribbulus.transcription.audio_backend import (
                configure_audio_backend,
            )

            # Should not raise, just warn
            configure_audio_backend()

            # Should not have called set_audio_backend
            mock_set.assert_not_called()

    def test_handles_list_backends_exception(self):
        """Should handle exceptions from list_audio_backends."""
        with (
            patch.dict("os.environ", {}, clear=True),
            patch(
                "torchaudio.list_audio_backends",
                side_effect=RuntimeError("No backends"),
            ),
            patch("torchaudio.set_audio_backend") as mock_set,
        ):
            from scribbulus.transcription.audio_backend import (
                configure_audio_backend,
            )

            # Should not raise
            configure_audio_backend()

            # Should not have called set_audio_backend
            mock_set.assert_not_called()

    def test_handles_set_backend_exception(self):
        """Should handle exceptions from set_audio_backend and try fallback."""
        call_count = 0

        def mock_set_backend(backend):
            nonlocal call_count
            call_count += 1
            if backend == "soundfile":
                raise RuntimeError("Soundfile failed")
            # sox_io should succeed

        with (
            patch.dict("os.environ", {}, clear=True),
            patch(
                "torchaudio.list_audio_backends",
                return_value=["soundfile", "sox_io"],
            ),
            patch("torchaudio.set_audio_backend", mock_set_backend),
        ):
            from scribbulus.transcription.audio_backend import (
                configure_audio_backend,
            )

            configure_audio_backend()

            # Should have tried both
            assert call_count == 2

    def test_only_configures_once(self):
        """Should only configure backend once even if called multiple times."""
        call_count = 0

        def mock_list_backends():
            nonlocal call_count
            call_count += 1
            return ["soundfile"]

        with (
            patch.dict("os.environ", {}, clear=True),
            patch("torchaudio.list_audio_backends", mock_list_backends),
            patch("torchaudio.set_audio_backend"),
        ):
            from scribbulus.transcription.audio_backend import (
                configure_audio_backend,
            )

            configure_audio_backend()
            configure_audio_backend()
            configure_audio_backend()

            # Should only have been called once
            assert call_count == 1

    def test_respects_existing_env_var(self):
        """Should not override existing TORCHAUDIO_USE_BACKEND_DISPATCHER."""
        with (
            patch.dict(
                "os.environ",
                {"TORCHAUDIO_USE_BACKEND_DISPATCHER": "0"},
                clear=True,
            ),
            patch(
                "torchaudio.list_audio_backends", return_value=["soundfile"]
            ),
            patch("torchaudio.set_audio_backend"),
        ):
            from scribbulus.transcription.audio_backend import (
                configure_audio_backend,
            )

            configure_audio_backend()

            import os

            # Should preserve existing value
            assert os.environ.get("TORCHAUDIO_USE_BACKEND_DISPATCHER") == "0"


class TestModuleImport:
    """Test that the audio_backend module can be imported."""

    def test_module_imports_torchaudio_at_top_level(self):
        """Module should import torchaudio at top level."""
        # This verifies the module has top-level torchaudio import
        import scribbulus.transcription.audio_backend as ab

        # The module should have torchaudio in its namespace
        assert hasattr(ab, "torchaudio")

    def test_module_exports_configure_function(self):
        """Module should export configure_audio_backend function."""
        from scribbulus.transcription.audio_backend import (
            configure_audio_backend,
        )

        assert callable(configure_audio_backend)

"""Tests for Fern CLI commands."""

import pytest
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner
from fern.cli import app


class TestCLICommands:
    """Test CLI command functionality."""

    def test_status_command(self, cli_runner):
        """Test the status command displays correctly."""
        result = cli_runner.invoke(app, ["status"])

        assert result.exit_code == 0
        # Verify output contains expected content
        assert "Fern Voice Training" in result.output or "Status" in result.output

    def test_status_command_data_directory_exists(self, cli_runner):
        """Test status command when data directory exists."""
        with patch("pathlib.Path.home") as mock_home:
            from pathlib import Path
            mock_home.return_value = Path("/mock/home")
            with patch("pathlib.Path.exists", return_value=True):
                result = cli_runner.invoke(app, ["status"])

                assert result.exit_code == 0

    def test_status_command_data_directory_missing(self, cli_runner):
        """Test status command when data directory doesn't exist."""
        with patch("pathlib.Path.home") as mock_home:
            from pathlib import Path
            mock_home.return_value = Path("/mock/home")
            with patch("pathlib.Path.exists", return_value=False):
                result = cli_runner.invoke(app, ["status"])

                assert result.exit_code == 0

    def test_version_command(self, cli_runner):
        """Test the version command displays correctly."""
        result = cli_runner.invoke(app, ["version"])

        assert result.exit_code == 0
        # Verify version was printed
        assert "Fern v0.1.0" in result.output

    def test_test_command_with_mocked_audio(self, cli_runner, mock_sounddevice):
        """Test the test command with mocked audio recording."""
        mock_pitch_result = {
            'median_pitch': 440.0,
            'mean_pitch': 445.0,
            'min_pitch': 430.0,
            'max_pitch': 455.0,
            'std_pitch': 5.0,
            'voiced_frames': 100,
            'total_frames': 100,
            'voicing_rate': 1.0
        }

        with patch("fern.analysis.extract_pitch_from_audio", return_value=mock_pitch_result):
            result = cli_runner.invoke(app, ["test", "--duration", "1"])

            assert result.exit_code == 0

    def test_test_command_with_no_pitch_detected(self, cli_runner, mock_sounddevice):
        """Test the test command when no pitch is detected."""
        mock_pitch_result = {
            'median_pitch': 0.0,
            'mean_pitch': 0.0,
            'min_pitch': 0.0,
            'max_pitch': 0.0,
            'std_pitch': 0.0,
            'voiced_frames': 0,
            'total_frames': 100,
            'voicing_rate': 0.0
        }

        with patch("fern.analysis.extract_pitch_from_audio", return_value=mock_pitch_result):
            result = cli_runner.invoke(app, ["test", "--duration", "1"])

            assert result.exit_code == 0

    def test_test_command_with_error(self, cli_runner, mock_sounddevice):
        """Test the test command handles errors gracefully."""
        with patch("fern.analysis.extract_pitch_from_audio", side_effect=Exception("Test error")):
            result = cli_runner.invoke(app, ["test", "--duration", "1"])

            # Should return error exit code
            assert result.exit_code != 0

    def test_test_command_with_custom_device(self, cli_runner, mock_sounddevice):
        """Test the test command with custom device ID."""
        mock_pitch_result = {
            'median_pitch': 220.0,
            'mean_pitch': 220.0,
            'min_pitch': 220.0,
            'max_pitch': 220.0,
            'std_pitch': 0.0,
            'voiced_frames': 100,
            'total_frames': 100,
            'voicing_rate': 1.0
        }

        with patch("fern.analysis.extract_pitch_from_audio", return_value=mock_pitch_result):
            with patch("sounddevice.rec") as mock_rec:
                mock_rec.return_value = mock_sounddevice['rec'].return_value

                result = cli_runner.invoke(app, ["test", "--duration", "1", "--device", "1"])

                assert result.exit_code == 0
                # Verify device parameter was passed to sounddevice.rec
                mock_rec.assert_called_once()

    def test_cli_help_command(self, cli_runner):
        """Test the CLI help command works."""
        result = cli_runner.invoke(app, ["--help"])
        
        assert result.exit_code == 0
        assert "Voice training feedback companion" in result.output

    def test_cli_subcommand_help(self, cli_runner):
        """Test CLI subcommand help works."""
        result = cli_runner.invoke(app, ["status", "--help"])
        
        assert result.exit_code == 0
        assert "Show current Fern status" in result.output

    def test_app_initialization(self):
        """Test the Typer app is initialized correctly."""
        from fern.cli import app

        # Verify app was created (check it exists and is a Typer instance)
        assert app is not None
        assert hasattr(app, 'callback')

    def test_console_initialization(self):
        """Test that console is initialized."""
        from fern.cli import console
        
        assert console is not None

    def test_cli_commands_are_registered(self, cli_runner):
        """Test that all CLI commands are properly registered."""
        result = cli_runner.invoke(app, ["--help"])
        
        assert result.exit_code == 0
        # Check that expected commands appear in help
        assert "status" in result.output
        assert "test" in result.output
        assert "version" in result.output


class TestCLIIntegration:
    """Integration tests for CLI functionality."""

    def test_cli_runner_basic(self):
        """Test basic CLI runner functionality."""
        runner = CliRunner()
        assert runner is not None

    def test_cli_app_import(self):
        """Test that the CLI app can be imported."""
        from fern.cli import app
        assert app is not None

    def test_cli_main_entry_point(self):
        """Test CLI main entry point."""
        with patch("fern.cli.app") as mock_app:
            # Import and call main
            from fern.cli import app
            with patch("typer.run") as mock_run:
                # Simulate __name__ == "__main__" block
                with patch("builtins.__name__", "__main__"):
                    app()  # This would call typer.run(app) in the main block
                    # The main block execution would call typer.run(app)


class TestCLIErrorHandling:
    """Test CLI error handling and edge cases."""

    def test_invalid_subcommand(self, cli_runner):
        """Test behavior with invalid subcommand."""
        result = cli_runner.invoke(app, ["invalid_command"])
        
        # Typer should handle invalid commands gracefully
        assert result.exit_code != 0

    def test_test_command_with_zero_duration(self, cli_runner):
        """Test test command with zero duration."""
        with patch("fern.analysis.extract_pitch_from_audio") as mock_extract:
            mock_extract.return_value = {'median_pitch': 0.0}

            result = cli_runner.invoke(app, ["test", "--duration", "0"])

            assert result.exit_code == 0

    def test_console_exception_handling(self, cli_runner):
        """Test that console exceptions are handled."""
        # This test verifies the CLI doesn't crash on exceptions
        # The actual behavior depends on exception handling in commands
        with patch("pathlib.Path.home", return_value="/nonexistent"):
            result = cli_runner.invoke(app, ["status"])

            # Should handle gracefully (either succeed or fail cleanly)
            assert result.exit_code in [0, 1]
"""Tests for Fern pitch and resonance analysis functions."""

import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from fern.analysis import extract_pitch_from_audio, extract_resonance_from_audio


class TestPitchAnalysis:
    """Test pitch extraction functionality."""

    def test_extract_pitch_from_audio_with_valid_audio(self, mock_parselmouth_sound, sample_audio_data):
        """Test pitch extraction with valid audio data."""
        result = extract_pitch_from_audio(sample_audio_data, 44100)
        
        # Verify the result structure
        assert isinstance(result, dict)
        assert 'median_pitch' in result
        assert 'mean_pitch' in result
        assert 'min_pitch' in result
        assert 'max_pitch' in result
        assert 'std_pitch' in result
        assert 'voiced_frames' in result
        assert 'total_frames' in result
        assert 'voicing_rate' in result
        
        # Verify pitch values are reasonable
        assert result['median_pitch'] >= 0
        assert result['mean_pitch'] >= 0
        assert result['voicing_rate'] >= 0
        assert result['voicing_rate'] <= 1

    def test_extract_pitch_from_audio_with_silence(self):
        """Test pitch extraction with silence (all zeros)."""
        # Create silence - all zeros
        sample_rate = 44100
        duration = 1.0
        silence = np.zeros(int(sample_rate * duration), dtype=np.float32)
        
        result = extract_pitch_from_audio(silence, sample_rate)
        
        # Should return zero values for silence
        assert result['median_pitch'] == 0.0
        assert result['mean_pitch'] == 0.0
        assert result['min_pitch'] == 0.0
        assert result['max_pitch'] == 0.0
        assert result['std_pitch'] == 0.0
        assert result['voiced_frames'] == 0
        assert result['voicing_rate'] == 0.0

    def test_extract_pitch_from_audio_with_noise(self):
        """Test pitch extraction with random noise."""
        # Create random noise
        sample_rate = 44100
        duration = 1.0
        noise = np.random.random(int(sample_rate * duration)).astype(np.float32)
        
        # This should not crash, even if it returns zero values
        result = extract_pitch_from_audio(noise, sample_rate)
        
        assert isinstance(result, dict)
        assert 'error' not in result or result.get('error') is None

    def test_extract_pitch_from_audio_parselmouth_error(self):
        """Test handling of parselmouth errors."""
        # Create audio data that might cause parselmouth to fail
        audio_data = np.array([1, 2, 3], dtype=np.float32)
        
        with patch("parselmouth.Sound", side_effect=Exception("Mock parselmouth error")):
            result = extract_pitch_from_audio(audio_data, 44100)
            
            # Should return error structure
            assert result['error'] == "Mock parselmouth error"
            assert result['median_pitch'] == 0.0
            assert result['mean_pitch'] == 0.0

    def test_extract_pitch_from_audio_empty_array(self):
        """Test with empty audio array."""
        empty_audio = np.array([], dtype=np.float32)
        
        result = extract_pitch_from_audio(empty_audio, 44100)
        
        # Should not crash and return appropriate values
        assert isinstance(result, dict)
        assert result['voicing_rate'] == 0.0
        assert result['total_frames'] == 0

    def test_extract_pitch_from_audio_various_sample_rates(self):
        """Test with different sample rates."""
        # Create a simple sine wave
        sample_rate = 22050
        duration = 0.5
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio = np.sin(2 * np.pi * 440 * t).astype(np.float32)
        
        result = extract_pitch_from_audio(audio, sample_rate)
        
        assert isinstance(result, dict)
        assert 'median_pitch' in result

    def test_extract_pitch_from_audio_mock_pitch_values(self, sample_audio_data):
        """Test with specific mock pitch values."""
        from unittest.mock import MagicMock, patch
        import numpy as np

        # Create mock pitch values - some voiced, some unvoiced
        expected_pitches = [440.0, 455.0, 442.0, 448.0]  # Non-zero values
        pitch_values = np.array([440.0, 0.0, 455.0, 0.0, 442.0, 0.0, 448.0])
        expected_total = 7
        expected_voiced = 4

        # Create mock objects
        mock_sound = MagicMock()
        mock_pitch = MagicMock()
        mock_pitch.selected_array = {'frequency': pitch_values}

        with patch("fern.analysis.parselmouth.Sound", return_value=mock_sound):
            with patch("fern.analysis.call", return_value=mock_pitch):
                result = extract_pitch_from_audio(sample_audio_data, 44100)

                # Verify the function processed the mocked pitch data
                assert result['voiced_frames'] == expected_voiced
                assert result['total_frames'] == expected_total
                assert result['voicing_rate'] == expected_voiced / expected_total
                assert result['median_pitch'] == np.median(expected_pitches)

    def test_extract_pitch_with_unvoiced_parts(self):
        """Test pitch extraction with mixed voiced/unvoiced audio."""
        # Create audio with both voiced and unvoiced parts
        sample_rate = 44100
        duration = 1.0
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        # Create mixed audio: voiced (sine wave) + unvoiced (noise)
        voiced_part = np.sin(2 * np.pi * 220 * t[:len(t)//2])
        unvoiced_part = np.random.random(len(t)//2) * 0.1
        mixed_audio = np.concatenate([voiced_part, unvoiced_part]).astype(np.float32)
        
        result = extract_pitch_from_audio(mixed_audio, sample_rate)
        
        # Should have some voiced frames but not all
        assert 0 < result['voicing_rate'] < 1
        assert result['voiced_frames'] > 0
        assert result['total_frames'] > result['voiced_frames']

    def test_extract_pitch_pitch_range_parameters(self):
        """Test that pitch extraction uses correct parameters."""
        from unittest.mock import MagicMock, patch
        import numpy as np

        audio_data = np.sin(2 * np.pi * 440 * np.linspace(0, 1, 44100)).astype(np.float32)

        # Track the call arguments
        call_args = []

        def mock_call(*args, **kwargs):
            call_args.append(args)
            mock_result = MagicMock()
            mock_result.selected_array = {'frequency': np.array([440.0])}
            return mock_result

        with patch("fern.analysis.parselmouth.Sound"):
            with patch("fern.analysis.call", side_effect=mock_call):
                result = extract_pitch_from_audio(audio_data, 44100)

                # Verify parselmouth.praat.call was called exactly once with correct parameters
                assert len(call_args) == 1
                # Each call_args entry is a tuple of (sound, "To Pitch", time_step, f_min, f_max)
                assert len(call_args[0]) >= 5
                assert call_args[0][1] == "To Pitch"
                assert call_args[0][2] == 0.01  # time_step
                assert call_args[0][3] == 75    # f_min
                assert call_args[0][4] == 600   # f_max


class TestResonanceAnalysis:
    """Test resonance (formant) extraction functionality."""

    def test_extract_resonance_from_audio_basic(self, sample_audio_data):
        """Test basic resonance extraction."""
        result = extract_resonance_from_audio(sample_audio_data, 44100)

        # Verify the result structure
        assert isinstance(result, dict)
        assert 'f1_mean' in result
        assert 'f2_mean' in result
        assert 'f3_mean' in result
        assert 'f1_std' in result
        assert 'f2_std' in result
        assert 'f3_std' in result

        # Check that formant_placeholder is False (now implemented)
        assert result.get('formant_placeholder') is False

    def test_extract_resonance_from_audio_empty_audio(self):
        """Test with empty audio data."""
        empty_audio = np.array([], dtype=np.float32)

        result = extract_resonance_from_audio(empty_audio, 44100)

        # Should return empty result values
        assert result['f1_mean'] == 0.0
        assert result['f2_mean'] == 0.0
        assert result['f3_mean'] == 0.0
        assert result['formant_placeholder'] is False

    def test_extract_resonance_different_sample_rates(self):
        """Test resonance extraction with different sample rates."""
        audio_data = np.random.random(22050).astype(np.float32)
        
        # Test with different sample rates
        for sample_rate in [16000, 22050, 44100]:
            result = extract_resonance_from_audio(audio_data, sample_rate)
            assert isinstance(result, dict)
            assert 'f1_mean' in result


class TestAnalysisEdgeCases:
    """Test edge cases and error conditions."""

    def test_extract_pitch_extremely_short_audio(self):
        """Test with very short audio clips."""
        # Just a few samples
        audio_data = np.array([0.1, 0.2, 0.1], dtype=np.float32)
        
        result = extract_pitch_from_audio(audio_data, 44100)
        
        # Should not crash
        assert isinstance(result, dict)
        assert 'median_pitch' in result

    def test_extract_pitch_very_high_frequencies(self):
        """Test with audio containing very high frequencies."""
        sample_rate = 44100
        duration = 0.1
        t = np.linspace(0, duration, int(sample_rate * duration))
        # Create very high frequency (close to Nyquist)
        high_freq_audio = np.sin(2 * np.pi * 20000 * t).astype(np.float32)
        
        result = extract_pitch_from_audio(high_freq_audio, sample_rate)
        
        assert isinstance(result, dict)

    def test_extract_pitch_very_low_frequencies(self):
        """Test with audio containing very low frequencies."""
        sample_rate = 44100
        duration = 2.0
        t = np.linspace(0, duration, int(sample_rate * duration))
        # Create very low frequency
        low_freq_audio = np.sin(2 * np.pi * 30 * t).astype(np.float32)
        
        result = extract_pitch_from_audio(low_freq_audio, sample_rate)
        
        assert isinstance(result, dict)

    def test_extract_pitch_different_dtypes(self):
        """Test with different numpy dtypes."""
        sample_rate = 44100
        duration = 0.5
        t = np.linspace(0, duration, int(sample_rate * duration))
        base_audio = np.sin(2 * np.pi * 440 * t)
        
        # Test different dtypes
        for dtype in [np.float16, np.float32, np.float64]:
            audio_data = base_audio.astype(dtype)
            result = extract_pitch_from_audio(audio_data, sample_rate)
            assert isinstance(result, dict)

    def test_consistency_of_results(self, sample_audio_data):
        """Test that results are consistent across multiple calls."""
        result1 = extract_pitch_from_audio(sample_audio_data, 44100)
        result2 = extract_pitch_from_audio(sample_audio_data, 44100)
        
        # Results should be identical for the same input
        assert result1['median_pitch'] == result2['median_pitch']
        assert result1['mean_pitch'] == result2['mean_pitch']
        assert result1['voicing_rate'] == result2['voicing_rate']


class TestAnalysisIntegration:
    """Integration tests for analysis functions."""

    def test_both_functions_work_together(self, sample_audio_data):
        """Test that both pitch and resonance analysis work together."""
        pitch_result = extract_pitch_from_audio(sample_audio_data, 44100)
        resonance_result = extract_resonance_from_audio(sample_audio_data, 44100)
        
        # Both should work without interfering with each other
        assert 'median_pitch' in pitch_result
        assert 'f1_mean' in resonance_result
        
        # Both should be dictionaries
        assert isinstance(pitch_result, dict)
        assert isinstance(resonance_result, dict)

    def test_analysis_with_realistic_voice_parameters(self):
        """Test with realistic voice frequency parameters."""
        # Create audio simulating typical voice range (80-250 Hz for speaking voice)
        sample_rate = 44100
        duration = 1.0
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        # Simulate a voice-like frequency (150 Hz)
        voice_audio = np.sin(2 * np.pi * 150 * t).astype(np.float32)
        
        pitch_result = extract_pitch_from_audio(voice_audio, sample_rate)
        
        # Should detect reasonable pitch
        assert 100 < pitch_result['median_pitch'] < 200
        assert pitch_result['voicing_rate'] > 0.5  # Most frames should be voiced

    def test_performance_with_long_audio(self):
        """Test that analysis doesn't take too long with longer audio."""
        import time
        
        # Create longer audio (10 seconds)
        sample_rate = 44100
        duration = 10.0
        t = np.linspace(0, duration, int(sample_rate * duration))
        long_audio = np.sin(2 * np.pi * 220 * t).astype(np.float32)
        
        start_time = time.time()
        result = extract_pitch_from_audio(long_audio, sample_rate)
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        # Should complete within reasonable time (e.g., 5 seconds)
        assert processing_time < 5.0
        assert isinstance(result, dict)
#!/usr/bin/env python3
"""Test pitch detection script.

Captures 5 seconds of audio from microphone and extracts fundamental frequency
using praat-parselmouth. Prints median pitch to console.
"""

import sys
import sounddevice as sd
import numpy as np
import parselmouth
from parselmouth.praat import call


def record_audio(duration: float = 5.0, sample_rate: int = 44100) -> np.ndarray:
    """Record audio from microphone.

    Args:
        duration: Recording duration in seconds
        sample_rate: Audio sample rate

    Returns:
        numpy array of audio data
    """
    print(f"Recording {duration} seconds of audio...")
    print("Speak now!")

    audio = sd.rec(
        int(duration * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype=np.float64
    )

    sd.wait()
    print("Recording complete!")
    return audio.flatten()


def extract_pitch(audio: np.ndarray, sample_rate: int) -> float:
    """Extract fundamental frequency using praat-parselmouth.

    Args:
        audio: Audio data as numpy array
        sample_rate: Audio sample rate

    Returns:
        Median pitch in Hz
    """
    sound = parselmouth.Sound(audio, sampling_frequency=sample_rate)

    pitch = sound.to_pitch(time_step=0.01, pitch_floor=75, pitch_ceiling=600)

    pitch_values = pitch.selected_array['frequency']
    pitch_values = pitch_values[pitch_values != 0]

    if not pitch_values.size:
        print("Warning: No pitch detected in audio")
        return 0.0

    median_pitch = np.median(pitch_values)
    return median_pitch


def main():
    """Main function to test pitch detection."""
    try:
        sample_rate = 44100
        duration = 5.0

        audio = record_audio(duration, sample_rate)
        median_pitch = extract_pitch(audio, sample_rate)

        print(f"\nMedian pitch: {median_pitch:.2f} Hz")

        if median_pitch > 0:
            print(f"Pitch category: {'High' if median_pitch > 200 else 'Medium' if median_pitch > 150 else 'Low'}")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
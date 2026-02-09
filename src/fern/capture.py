"""Audio capture module.

Handles real-time audio capture from the microphone during dictation sessions.
"""

import os
import shutil
import wave
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional, List, Tuple
import numpy as np
import sounddevice as sd
import soundfile as sf


class AudioCaptureError(Exception):
    """Base exception for audio capture errors."""
    pass


class AudioDeviceError(AudioCaptureError):
    """Raised when audio device is not available."""
    pass


class ClipStorage:
    """Manages audio clip storage with rolling archive."""

    def __init__(
        self,
        clips_dir: Optional[Path] = None,
        max_clips: int = 30,
        max_storage_mb: int = 500
    ):
        """Initialize clip storage.

        Args:
            clips_dir: Directory for storing clips (default: ~/.fern/clips)
            max_clips: Maximum number of clips to keep
            max_storage_mb: Maximum total storage in MB
        """
        if clips_dir is None:
            clips_dir = Path.home() / ".fern" / "clips"
        self.clips_dir = Path(clips_dir)
        self.max_clips = max_clips
        self.max_storage_mb = max_storage_mb
        self.current_quarter_dir: Optional[Path] = None
        
        # Ensure directory exists
        self.clips_dir.mkdir(parents=True, exist_ok=True)
        
        # Set current quarter directory
        self._set_current_quarter_dir()

    def _set_current_quarter_dir(self) -> None:
        """Set the directory for the current quarter."""
        now = datetime.now()
        quarter = (now.month - 1) // 3 + 1
        quarter_name = f"Q{quarter}-{now.year}"
        self.current_quarter_dir = self.clips_dir / quarter_name
        self.current_quarter_dir.mkdir(parents=True, exist_ok=True)

    def _get_storage_size_mb(self) -> float:
        """Get total storage used in MB."""
        total_size = 0
        for root, dirs, files in os.walk(self.clips_dir):
            for file in files:
                file_path = Path(root) / file
                total_size += file_path.stat().st_size
        return total_size / (1024 * 1024)

    def _get_all_clips(self) -> List[Tuple[Path, datetime]]:
        """Get all clips with their modification times.

        Returns:
            List of (clip_path, creation_time) tuples.
        """
        clips = []
        for root, dirs, files in os.walk(self.clips_dir):
            for file in files:
                if file.endswith('.wav'):
                    file_path = Path(root) / file
                    # Use stat to get modification time
                    mtime = file_path.stat().st_mtime
                    clips.append((file_path, datetime.fromtimestamp(mtime)))
        return sorted(clips, key=lambda x: x[1])

    def _enforce_limits(self) -> None:
        """Enforce storage limits by removing oldest clips."""
        # Enforce max_clips
        all_clips = self._get_all_clips()
        while len(all_clips) > self.max_clips:
            oldest_clip, _ = all_clips.pop(0)
            oldest_clip.unlink()
            print(f"Removed old clip: {oldest_clip}")

        # Enforce max_storage_mb
        while self._get_storage_size_mb() > self.max_storage_mb and all_clips:
            oldest_clip, _ = all_clips.pop(0)
            oldest_clip.unlink()
            print(f"Removed oversized clip: {oldest_clip}")

    def save_clip(
        self,
        audio_data: np.ndarray,
        sample_rate: int,
        session_id: Optional[int] = None,
        reading_id: Optional[int] = None
    ) -> Path:
        """Save an audio clip.

        Args:
            audio_data: Audio data as numpy array
            sample_rate: Sample rate in Hz
            session_id: Optional session ID for naming
            reading_id: Optional reading ID for naming

        Returns:
            Path to the saved clip.
        """
        # Check if we need to switch quarters
        self._set_current_quarter_dir()
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        if session_id is not None and reading_id is not None:
            filename = f"session_{session_id}_reading_{reading_id}_{timestamp}.wav"
        elif session_id is not None:
            filename = f"session_{session_id}_{timestamp}.wav"
        else:
            filename = f"clip_{timestamp}.wav"
        
        clip_path = self.current_quarter_dir / filename
        
        # Ensure output directory exists
        clip_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save as WAV
        sf.write(str(clip_path), audio_data, sample_rate)
        
        # Enforce storage limits
        self._enforce_limits()
        
        return clip_path

    def list_clips(
        self,
        quarter: Optional[str] = None,
        limit: int = 50
    ) -> List[Path]:
        """List available clips.

        Args:
            quarter: Optional quarter to list (e.g., "Q1-2026")
            limit: Maximum number of clips to return

        Returns:
            List of clip paths.
        """
        if quarter:
            search_dir = self.clips_dir / quarter
        else:
            search_dir = self.clips_dir
        
        if not search_dir.exists():
            return []
        
        clips = []
        for root, dirs, files in os.walk(search_dir):
            for file in sorted(files, reverse=True):
                if file.endswith('.wav'):
                    clips.append(Path(root) / file)
                    if len(clips) >= limit:
                        return clips
        return clips

    def get_clip(self, clip_path: str) -> Tuple[np.ndarray, int]:
        """Load an audio clip.

        Args:
            clip_path: Path to the clip file

        Returns:
            Tuple of (audio_data, sample_rate)
        """
        audio_data, sample_rate = sf.read(clip_path)
        return audio_data, sample_rate

    def delete_clip(self, clip_path: Path) -> bool:
        """Delete a clip.

        Args:
            clip_path: Path to the clip to delete

        Returns:
            True if deleted successfully.
        """
        if clip_path.exists():
            clip_path.unlink()
            return True
        return False

    def archive_old_quarter(self, quarter: str) -> Optional[Path]:
        """Archive a quarter directory.

        Args:
            quarter: Quarter to archive (e.g., "Q4-2025")

        Returns:
            Path to the archive or None if not found.
        """
        quarter_dir = self.clips_dir / quarter
        if not quarter_dir.exists():
            return None
        
        # Create archive
        archive_name = f"{quarter}_archived"
        archive_dir = self.clips_dir / archive_name
        
        if archive_dir.exists():
            shutil.rmtree(archive_dir)
        
        shutil.move(str(quarter_dir), str(archive_dir))
        return archive_dir


class AudioRecorder:
    """Audio recorder with callback support for real-time monitoring."""

    def __init__(
        self,
        sample_rate: int = 44100,
        channels: int = 1,
        dtype: np.dtype = np.float32,
        storage: Optional[ClipStorage] = None
    ):
        """Initialize the audio recorder.

        Args:
            sample_rate: Sample rate in Hz (default: 44100)
            channels: Number of audio channels (default: 1)
            dtype: NumPy dtype for audio data
            storage: Optional ClipStorage for saving clips
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.dtype = dtype
        self.storage = storage
        
        self._stream: Optional[sd.InputStream] = None
        self._is_recording = False
        self._audio_buffer: List[np.ndarray] = []
        self._callback: Optional[Callable[[np.ndarray], None]] = None

    def list_devices(self) -> List[dict]:
        """List available audio input devices.

        Returns:
            List of device dictionaries with id, name, etc.
        """
        devices = sd.query_devices()
        input_devices = [
            {
                'id': d['index'],
                'name': d['name'],
                'channels': d['max_input_channels'],
                'default_samplerate': d.get('default_samplerate', 44100)
            }
            for d in devices if d['max_input_channels'] > 0
        ]
        return input_devices

    def get_default_device(self) -> Optional[dict]:
        """Get the default input device.

        Returns:
            Default device dict or None if not found.
        """
        devices = self.list_devices()
        if not devices:
            return None
        return devices[0]

    def _audio_callback(
        self,
        indata: np.ndarray,
        frames: int,
        time,
        status: sd.CallbackFlags
    ) -> None:
        """Internal audio callback for sounddevice."""
        if status:
            print(f"Audio callback status: {status}")
        
        self._audio_buffer.append(indata.copy())
        
        if self._callback is not None:
            self._callback(indata)

    def start_recording(
        self,
        device: Optional[int] = None,
        callback: Optional[Callable[[np.ndarray], None]] = None
    ) -> None:
        """Start audio recording.

        Args:
            device: Optional device ID
            callback: Optional callback function for real-time data

        Raises:
            AudioDeviceError: If device is not available.
        """
        if self._is_recording:
            return

        self._callback = callback
        self._audio_buffer = []

        try:
            self._stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype=self.dtype,
                callback=self._audio_callback,
                device=device,
                blocksize=1024
            )
            self._stream.start()
            self._is_recording = True
        except sd.PortAudioError as e:
            raise AudioDeviceError(f"Failed to open audio device: {e}")

    def stop_recording(self) -> np.ndarray:
        """Stop recording and return the captured audio.

        Returns:
            Captured audio as numpy array.
        """
        if not self._is_recording:
            return np.array([], dtype=self.dtype)

        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        self._is_recording = False
        self._callback = None

        # Concatenate all buffered frames
        if self._audio_buffer:
            return np.concatenate(self._audio_buffer)
        return np.array([], dtype=self.dtype)

    def record_for_duration(
        self,
        duration: float,
        device: Optional[int] = None
    ) -> np.ndarray:
        """Record audio for a fixed duration.

        Args:
            duration: Duration in seconds
            device: Optional device ID

        Returns:
            Captured audio as numpy array.
        """
        num_samples = int(self.sample_rate * duration)
        audio_data = np.zeros(num_samples, dtype=self.dtype)
        
        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype=self.dtype,
                device=device,
                blocksize=1024
            ) as stream:
                # Read audio in chunks
                remaining = num_samples
                offset = 0
                while remaining > 0:
                    chunk_size = min(1024, remaining)
                    chunk, _ = stream.read(chunk_size)
                    audio_data[offset:offset + chunk_size] = chunk.flatten()
                    offset += chunk_size
                    remaining -= chunk_size
        except sd.PortAudioError as e:
            raise AudioDeviceError(f"Failed to record audio: {e}")
        
        return audio_data

    def save_recording(
        self,
        audio_data: np.ndarray,
        session_id: Optional[int] = None,
        reading_id: Optional[int] = None
    ) -> Optional[Path]:
        """Save a recording using the storage.

        Args:
            audio_data: Audio data to save
            session_id: Optional session ID
            reading_id: Optional reading ID

        Returns:
            Path to saved clip or None if no storage configured.
        """
        if self.storage is None:
            return None
        return self.storage.save_clip(
            audio_data,
            self.sample_rate,
            session_id=session_id,
            reading_id=reading_id
        )


def get_default_storage() -> ClipStorage:
    """Get the default clip storage instance.

    Returns:
        ClipStorage instance configured for ~/.fern/clips
    """
    return ClipStorage()


def get_default_recorder() -> AudioRecorder:
    """Get the default audio recorder.

    Returns:
        AudioRecorder with default settings.
    """
    return AudioRecorder(storage=get_default_storage())

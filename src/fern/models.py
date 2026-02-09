"""Data models for Fern.

Dataclasses for Session, Reading, Target, and other core entities.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path


@dataclass
class Reading:
    """A single pitch/resonance reading from an audio sample."""
    id: Optional[int] = None
    session_id: Optional[int] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Pitch measurements (Hz)
    median_pitch: float = 0.0
    mean_pitch: float = 0.0
    min_pitch: float = 0.0
    max_pitch: float = 0.0
    std_pitch: float = 0.0
    
    # Voicing metrics
    voiced_frames: int = 0
    total_frames: int = 0
    voicing_rate: float = 0.0
    
    # Resonance measurements (formants in Hz)
    f1_mean: float = 0.0
    f2_mean: float = 0.0
    f3_mean: float = 0.0
    f1_std: float = 0.0
    f2_std: float = 0.0
    f3_std: float = 0.0
    
    # Audio clip path
    clip_path: Optional[str] = None
    
    # Additional metadata
    duration_seconds: float = 0.0
    device_id: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'timestamp': self.timestamp.isoformat(),
            'median_pitch': self.median_pitch,
            'mean_pitch': self.mean_pitch,
            'min_pitch': self.min_pitch,
            'max_pitch': self.max_pitch,
            'std_pitch': self.std_pitch,
            'voiced_frames': self.voiced_frames,
            'total_frames': self.total_frames,
            'voicing_rate': self.voicing_rate,
            'f1_mean': self.f1_mean,
            'f2_mean': self.f2_mean,
            'f3_mean': self.f3_mean,
            'f1_std': self.f1_std,
            'f2_std': self.f2_std,
            'f3_std': self.f3_std,
            'clip_path': self.clip_path,
            'duration_seconds': self.duration_seconds,
            'device_id': self.device_id,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Reading':
        """Create from dictionary."""
        return cls(
            id=data.get('id'),
            session_id=data.get('session_id'),
            timestamp=datetime.fromisoformat(data['timestamp']) if isinstance(data.get('timestamp'), str) else data.get('timestamp', datetime.now()),
            median_pitch=data.get('median_pitch', 0.0),
            mean_pitch=data.get('mean_pitch', 0.0),
            min_pitch=data.get('min_pitch', 0.0),
            max_pitch=data.get('max_pitch', 0.0),
            std_pitch=data.get('std_pitch', 0.0),
            voiced_frames=data.get('voiced_frames', 0),
            total_frames=data.get('total_frames', 0),
            voicing_rate=data.get('voicing_rate', 0.0),
            f1_mean=data.get('f1_mean', 0.0),
            f2_mean=data.get('f2_mean', 0.0),
            f3_mean=data.get('f3_mean', 0.0),
            f1_std=data.get('f1_std', 0.0),
            f2_std=data.get('f2_std', 0.0),
            f3_std=data.get('f3_std', 0.0),
            clip_path=data.get('clip_path'),
            duration_seconds=data.get('duration_seconds', 0.0),
            device_id=data.get('device_id'),
        )


@dataclass
class Target:
    """Voice training target range."""
    id: Optional[int] = None
    name: str = "Default"
    created_at: datetime = field(default_factory=datetime.now)
    
    # Pitch range (Hz)
    min_pitch: float = 80.0
    max_pitch: float = 250.0
    
    # Target voice type (for context)
    voice_type: Optional[str] = None  # e.g., "speaking", "singing", "neutral"
    
    # Optional resonance targets (formant ratios)
    target_f2: Optional[float] = None  # Target F2 frequency
    
    # Whether this is the active target
    is_active: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            'id': self.id,
            'name': self.name,
            'created_at': self.created_at.isoformat(),
            'min_pitch': self.min_pitch,
            'max_pitch': self.max_pitch,
            'voice_type': self.voice_type,
            'target_f2': self.target_f2,
            'is_active': self.is_active,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Target':
        """Create from dictionary."""
        return cls(
            id=data.get('id'),
            name=data.get('name', 'Default'),
            created_at=datetime.fromisoformat(data['created_at']) if isinstance(data.get('created_at'), str) else data.get('created_at', datetime.now()),
            min_pitch=data.get('min_pitch', 80.0),
            max_pitch=data.get('max_pitch', 250.0),
            voice_type=data.get('voice_type'),
            target_f2=data.get('target_f2'),
            is_active=data.get('is_active', True),
        )


@dataclass
class Session:
    """A practice session containing multiple readings."""
    id: Optional[int] = None
    name: Optional[str] = None
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    target_id: Optional[int] = None
    
    # Session summary (computed from readings)
    reading_count: int = 0
    avg_median_pitch: float = 0.0
    avg_voicing_rate: float = 0.0
    
    # Notes
    notes: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            'id': self.id,
            'name': self.name,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'target_id': self.target_id,
            'reading_count': self.reading_count,
            'avg_median_pitch': self.avg_median_pitch,
            'avg_voicing_rate': self.avg_voicing_rate,
            'notes': self.notes,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Session':
        """Create from dictionary."""
        return cls(
            id=data.get('id'),
            name=data.get('name'),
            start_time=datetime.fromisoformat(data['start_time']) if isinstance(data.get('start_time'), str) else data.get('start_time', datetime.now()),
            end_time=datetime.fromisoformat(data['end_time']) if isinstance(data.get('end_time'), str) else data.get('end_time'),
            target_id=data.get('target_id'),
            reading_count=data.get('reading_count', 0),
            avg_median_pitch=data.get('avg_median_pitch', 0.0),
            avg_voicing_rate=data.get('avg_voicing_rate', 0.0),
            notes=data.get('notes'),
        )


@dataclass
class SessionSummary:
    """Aggregated statistics for a session or time period."""
    session_id: Optional[int] = None
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    
    # Reading stats
    total_readings: int = 0
    readings_in_range: int = 0
    readings_out_of_range: int = 0
    
    # Pitch stats
    avg_median_pitch: float = 0.0
    min_median_pitch: float = 0.0
    max_median_pitch: float = 0.0
    pitch_std: float = 0.0
    
    # Pitch range compliance
    in_range_percentage: float = 0.0
    
    # Trend (comparison to previous period)
    pitch_trend: Optional[str] = None  # "up", "down", "stable"
    pitch_trend_delta: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'session_id': self.session_id,
            'period_start': self.period_start.isoformat() if self.period_start else None,
            'period_end': self.period_end.isoformat() if self.period_end else None,
            'total_readings': self.total_readings,
            'readings_in_range': self.readings_in_range,
            'readings_out_of_range': self.readings_out_of_range,
            'avg_median_pitch': self.avg_median_pitch,
            'min_median_pitch': self.min_median_pitch,
            'max_median_pitch': self.max_median_pitch,
            'pitch_std': self.pitch_std,
            'in_range_percentage': self.in_range_percentage,
            'pitch_trend': self.pitch_trend,
            'pitch_trend_delta': self.pitch_trend_delta,
        }

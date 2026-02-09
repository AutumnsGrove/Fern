"""SQLite database interface.

Manages persistence for sessions, readings, targets, and configuration.
"""

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Generator, List, Optional, Tuple, Any

from .models import Session, Reading, Target, SessionSummary


class DatabaseError(Exception):
    """Base exception for database errors."""
    pass


class DatabaseNotFoundError(DatabaseError):
    """Raised when database file is not found."""
    pass


class SchemaError(DatabaseError):
    """Raised when there's a schema mismatch."""
    pass


class Database:
    """SQLite database manager for Fern data."""

    SCHEMA_VERSION = 1

    def __init__(self, db_path: Path):
        """Initialize database connection.

        Args:
            db_path: Path to the SQLite database file.
        """
        self.db_path = db_path
        self._ensure_parent_exists()

    def _ensure_parent_exists(self) -> None:
        """Ensure the database parent directory exists."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Get a database connection context manager."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def initialize(self) -> None:
        """Initialize the database schema."""
        with self.connection() as conn:
            cursor = conn.cursor()

            # Create sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    target_id INTEGER,
                    reading_count INTEGER DEFAULT 0,
                    avg_median_pitch REAL DEFAULT 0.0,
                    avg_voicing_rate REAL DEFAULT 0.0,
                    notes TEXT,
                    FOREIGN KEY (target_id) REFERENCES targets(id)
                )
            """)

            # Create readings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS readings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    timestamp TEXT NOT NULL,
                    median_pitch REAL DEFAULT 0.0,
                    mean_pitch REAL DEFAULT 0.0,
                    min_pitch REAL DEFAULT 0.0,
                    max_pitch REAL DEFAULT 0.0,
                    std_pitch REAL DEFAULT 0.0,
                    voiced_frames INTEGER DEFAULT 0,
                    total_frames INTEGER DEFAULT 0,
                    voicing_rate REAL DEFAULT 0.0,
                    f1_mean REAL DEFAULT 0.0,
                    f2_mean REAL DEFAULT 0.0,
                    f3_mean REAL DEFAULT 0.0,
                    f1_std REAL DEFAULT 0.0,
                    f2_std REAL DEFAULT 0.0,
                    f3_std REAL DEFAULT 0.0,
                    clip_path TEXT,
                    duration_seconds REAL DEFAULT 0.0,
                    device_id INTEGER,
                    FOREIGN KEY (session_id) REFERENCES sessions(id)
                )
            """)

            # Create targets table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS targets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL DEFAULT 'Default',
                    created_at TEXT NOT NULL,
                    min_pitch REAL NOT NULL DEFAULT 80.0,
                    max_pitch REAL NOT NULL DEFAULT 250.0,
                    voice_type TEXT,
                    target_f2 REAL,
                    is_active INTEGER DEFAULT 1
                )
            """)

            # Create metadata table for schema version
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)

            # Set schema version
            cursor.execute(
                "INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)",
                ('schema_version', str(self.SCHEMA_VERSION))
            )

            # Create default target if none exists
            cursor.execute("SELECT COUNT(*) FROM targets")
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    INSERT INTO targets (name, created_at, min_pitch, max_pitch, is_active)
                    VALUES (?, ?, ?, ?, ?)
                """, ('Default', datetime.now().isoformat(), 80.0, 250.0, 1))

    def check_schema(self) -> bool:
        """Check if the database schema is valid.

        Returns:
            True if schema is valid and current.
        """
        try:
            with self.connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT value FROM metadata WHERE key = ?", ('schema_version',))
                row = cursor.fetchone()
                if row is None:
                    return False
                return int(row[0]) == self.SCHEMA_VERSION
        except sqlite3.OperationalError:
            return False

    # Session operations

    def create_session(self, session: Session) -> int:
        """Create a new session.

        Args:
            session: Session object to create.

        Returns:
            ID of the newly created session.
        """
        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sessions (name, start_time, target_id, notes)
                VALUES (?, ?, ?, ?)
            """, (
                session.name,
                session.start_time.isoformat(),
                session.target_id,
                session.notes
            ))
            return cursor.lastrowid

    def get_session(self, session_id: int) -> Optional[Session]:
        """Get a session by ID.

        Args:
            session_id: ID of the session to retrieve.

        Returns:
            Session object or None if not found.
        """
        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
            row = cursor.fetchone()
            if row is None:
                return None
            return Session(
                id=row['id'],
                name=row['name'],
                start_time=datetime.fromisoformat(row['start_time']),
                end_time=datetime.fromisoformat(row['end_time']) if row['end_time'] else None,
                target_id=row['target_id'],
                reading_count=row['reading_count'],
                avg_median_pitch=row['avg_median_pitch'],
                avg_voicing_rate=row['avg_voicing_rate'],
                notes=row['notes'],
            )

    def update_session(self, session: Session) -> None:
        """Update an existing session.

        Args:
            session: Session object to update.
        """
        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE sessions SET
                    name = ?,
                    end_time = ?,
                    target_id = ?,
                    reading_count = ?,
                    avg_median_pitch = ?,
                    avg_voicing_rate = ?,
                    notes = ?
                WHERE id = ?
            """, (
                session.name,
                session.end_time.isoformat() if session.end_time else None,
                session.target_id,
                session.reading_count,
                session.avg_median_pitch,
                session.avg_voicing_rate,
                session.notes,
                session.id
            ))

    def list_sessions(
        self,
        limit: int = 50,
        offset: int = 0,
        target_id: Optional[int] = None
    ) -> List[Session]:
        """List sessions with optional filtering.

        Args:
            limit: Maximum number of sessions to return.
            offset: Number of sessions to skip.
            target_id: Optional target ID to filter by.

        Returns:
            List of Session objects.
        """
        with self.connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM sessions"
            params = []
            if target_id is not None:
                query += " WHERE target_id = ?"
                params.append(target_id)
            query += " ORDER BY start_time DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor.execute(query, params)
            return [
                Session(
                    id=row['id'],
                    name=row['name'],
                    start_time=datetime.fromisoformat(row['start_time']),
                    end_time=datetime.fromisoformat(row['end_time']) if row['end_time'] else None,
                    target_id=row['target_id'],
                    reading_count=row['reading_count'],
                    avg_median_pitch=row['avg_median_pitch'],
                    avg_voicing_rate=row['avg_voicing_rate'],
                    notes=row['notes'],
                )
                for row in cursor.fetchall()
            ]

    def get_recent_sessions(self, count: int = 10) -> List[Session]:
        """Get the most recent sessions.

        Args:
            count: Number of sessions to return.

        Returns:
            List of recent Session objects.
        """
        return self.list_sessions(limit=count)

    # Reading operations

    def create_reading(self, reading: Reading) -> int:
        """Create a new reading.

        Args:
            reading: Reading object to create.

        Returns:
            ID of the newly created reading.
        """
        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO readings (
                    session_id, timestamp, median_pitch, mean_pitch, min_pitch,
                    max_pitch, std_pitch, voiced_frames, total_frames, voicing_rate,
                    f1_mean, f2_mean, f3_mean, f1_std, f2_std, f3_std,
                    clip_path, duration_seconds, device_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                reading.session_id,
                reading.timestamp.isoformat(),
                reading.median_pitch,
                reading.mean_pitch,
                reading.min_pitch,
                reading.max_pitch,
                reading.std_pitch,
                reading.voiced_frames,
                reading.total_frames,
                reading.voicing_rate,
                reading.f1_mean,
                reading.f2_mean,
                reading.f3_mean,
                reading.f1_std,
                reading.f2_std,
                reading.f3_std,
                reading.clip_path,
                reading.duration_seconds,
                reading.device_id
            ))
            return cursor.lastrowid

    def get_reading(self, reading_id: int) -> Optional[Reading]:
        """Get a reading by ID.

        Args:
            reading_id: ID of the reading to retrieve.

        Returns:
            Reading object or None if not found.
        """
        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM readings WHERE id = ?", (reading_id,))
            row = cursor.fetchone()
            if row is None:
                return None
            return Reading(
                id=row['id'],
                session_id=row['session_id'],
                timestamp=datetime.fromisoformat(row['timestamp']),
                median_pitch=row['median_pitch'],
                mean_pitch=row['mean_pitch'],
                min_pitch=row['min_pitch'],
                max_pitch=row['max_pitch'],
                std_pitch=row['std_pitch'],
                voiced_frames=row['voiced_frames'],
                total_frames=row['total_frames'],
                voicing_rate=row['voicing_rate'],
                f1_mean=row['f1_mean'],
                f2_mean=row['f2_mean'],
                f3_mean=row['f3_mean'],
                f1_std=row['f1_std'],
                f2_std=row['f2_std'],
                f3_std=row['f3_std'],
                clip_path=row['clip_path'],
                duration_seconds=row['duration_seconds'],
                device_id=row['device_id'],
            )

    def get_readings_for_session(self, session_id: int) -> List[Reading]:
        """Get all readings for a session.

        Args:
            session_id: ID of the session.

        Returns:
            List of Reading objects.
        """
        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM readings WHERE session_id = ? ORDER BY timestamp",
                (session_id,)
            )
            return [
                Reading(
                    id=row['id'],
                    session_id=row['session_id'],
                    timestamp=datetime.fromisoformat(row['timestamp']),
                    median_pitch=row['median_pitch'],
                    mean_pitch=row['mean_pitch'],
                    min_pitch=row['min_pitch'],
                    max_pitch=row['max_pitch'],
                    std_pitch=row['std_pitch'],
                    voiced_frames=row['voiced_frames'],
                    total_frames=row['total_frames'],
                    voicing_rate=row['voicing_rate'],
                    f1_mean=row['f1_mean'],
                    f2_mean=row['f2_mean'],
                    f3_mean=row['f3_mean'],
                    f1_std=row['f1_std'],
                    f2_std=row['f2_std'],
                    f3_std=row['f3_std'],
                    clip_path=row['clip_path'],
                    duration_seconds=row['duration_seconds'],
                    device_id=row['device_id'],
                )
                for row in cursor.fetchall()
            ]

    def get_recent_readings(self, count: int = 100) -> List[Reading]:
        """Get the most recent readings across all sessions.

        Args:
            count: Maximum number of readings to return.

        Returns:
            List of recent Reading objects.
        """
        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM readings ORDER BY timestamp DESC LIMIT ?",
                (count,)
            )
            return [
                Reading(
                    id=row['id'],
                    session_id=row['session_id'],
                    timestamp=datetime.fromisoformat(row['timestamp']),
                    median_pitch=row['median_pitch'],
                    mean_pitch=row['mean_pitch'],
                    min_pitch=row['min_pitch'],
                    max_pitch=row['max_pitch'],
                    std_pitch=row['std_pitch'],
                    voiced_frames=row['voiced_frames'],
                    total_frames=row['total_frames'],
                    voicing_rate=row['voicing_rate'],
                    f1_mean=row['f1_mean'],
                    f2_mean=row['f2_mean'],
                    f3_mean=row['f3_mean'],
                    f1_std=row['f1_std'],
                    f2_std=row['f2_std'],
                    f3_std=row['f3_std'],
                    clip_path=row['clip_path'],
                    duration_seconds=row['duration_seconds'],
                    device_id=row['device_id'],
                )
                for row in cursor.fetchall()
            ]

    # Target operations

    def create_target(self, target: Target) -> int:
        """Create a new target.

        Args:
            target: Target object to create.

        Returns:
            ID of the newly created target.
        """
        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO targets (name, created_at, min_pitch, max_pitch, voice_type, target_f2, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                target.name,
                target.created_at.isoformat(),
                target.min_pitch,
                target.max_pitch,
                target.voice_type,
                target.target_f2,
                1 if target.is_active else 0
            ))
            return cursor.lastrowid

    def get_target(self, target_id: int) -> Optional[Target]:
        """Get a target by ID.

        Args:
            target_id: ID of the target to retrieve.

        Returns:
            Target object or None if not found.
        """
        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM targets WHERE id = ?", (target_id,))
            row = cursor.fetchone()
            if row is None:
                return None
            return Target(
                id=row['id'],
                name=row['name'],
                created_at=datetime.fromisoformat(row['created_at']),
                min_pitch=row['min_pitch'],
                max_pitch=row['max_pitch'],
                voice_type=row['voice_type'],
                target_f2=row['target_f2'],
                is_active=bool(row['is_active']),
            )

    def get_active_target(self) -> Optional[Target]:
        """Get the currently active target.

        Returns:
            Active Target object or None if no target is active.
        """
        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM targets WHERE is_active = 1 ORDER BY created_at DESC LIMIT 1")
            row = cursor.fetchone()
            if row is None:
                return None
            return Target(
                id=row['id'],
                name=row['name'],
                created_at=datetime.fromisoformat(row['created_at']),
                min_pitch=row['min_pitch'],
                max_pitch=row['max_pitch'],
                voice_type=row['voice_type'],
                target_f2=row['target_f2'],
                is_active=bool(row['is_active']),
            )

    def list_targets(self) -> List[Target]:
        """List all targets.

        Returns:
            List of Target objects.
        """
        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM targets ORDER BY created_at DESC")
            return [
                Target(
                    id=row['id'],
                    name=row['name'],
                    created_at=datetime.fromisoformat(row['created_at']),
                    min_pitch=row['min_pitch'],
                    max_pitch=row['max_pitch'],
                    voice_type=row['voice_type'],
                    target_f2=row['target_f2'],
                    is_active=bool(row['is_active']),
                )
                for row in cursor.fetchall()
            ]

    def set_active_target(self, target_id: int) -> None:
        """Set a target as active, deactivating others.

        Args:
            target_id: ID of the target to activate.
        """
        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE targets SET is_active = 0")
            cursor.execute("UPDATE targets SET is_active = 1 WHERE id = ?", (target_id,))

    # Statistics and aggregation

    def get_session_summary(self, session_id: int, target: Optional[Target] = None) -> SessionSummary:
        """Get aggregated statistics for a session.

        Args:
            session_id: ID of the session.
            target: Optional target for range comparison.

        Returns:
            SessionSummary with aggregated statistics.
        """
        with self.connection() as conn:
            cursor = conn.cursor()

            # Get reading count
            cursor.execute("SELECT COUNT(*) FROM readings WHERE session_id = ?", (session_id,))
            total_readings = cursor.fetchone()[0]

            if total_readings == 0:
                return SessionSummary(session_id=session_id)

            # Get pitch statistics
            cursor.execute("""
                SELECT
                    AVG(median_pitch) as avg_pitch,
                    MIN(median_pitch) as min_pitch,
                    MAX(median_pitch) as max_pitch,
                    AVG(std_pitch) as avg_std,
                    AVG(voicing_rate) as avg_voicing
                FROM readings
                WHERE session_id = ?
            """, (session_id,))
            row = cursor.fetchone()

            avg_pitch = row['avg_pitch'] or 0.0
            min_pitch = row['min_pitch'] or 0.0
            max_pitch = row['max_pitch'] or 0.0
            pitch_std = row['avg_std'] or 0.0
            avg_voicing = row['avg_voicing'] or 0.0

            # Count readings in range if target provided
            readings_in_range = 0
            if target and target.min_pitch > 0:
                cursor.execute("""
                    SELECT COUNT(*) FROM readings
                    WHERE session_id = ? AND median_pitch >= ? AND median_pitch <= ?
                """, (session_id, target.min_pitch, target.max_pitch))
                readings_in_range = cursor.fetchone()[0]

            in_range_pct = (readings_in_range / total_readings * 100) if total_readings > 0 else 0.0

            return SessionSummary(
                session_id=session_id,
                total_readings=total_readings,
                readings_in_range=readings_in_range,
                readings_out_of_range=total_readings - readings_in_range,
                avg_median_pitch=avg_pitch,
                min_median_pitch=min_pitch,
                max_median_pitch=max_pitch,
                pitch_std=pitch_std,
                avg_voicing_rate=avg_voicing,
                in_range_percentage=in_range_pct,
            )

    def get_trend_data(
        self,
        days: int = 30,
        target_id: Optional[int] = None
    ) -> List[Tuple[datetime, float]]:
        """Get daily average pitch for trend analysis.

        Args:
            days: Number of days of history to include.
            target_id: Optional target ID to filter by.

        Returns:
            List of (date, average_pitch) tuples.
        """
        with self.connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT date(timestamp) as date, AVG(median_pitch) as avg_pitch
                FROM readings
                WHERE timestamp >= datetime('now', ?)
            """
            params = [f'-{days} days']

            if target_id is not None:
                query += """ AND session_id IN (
                    SELECT id FROM sessions WHERE target_id = ?
                )"""
                params.append(target_id)

            query += " GROUP BY date(timestamp) ORDER BY date"

            cursor.execute(query, params)
            return [
                (datetime.fromisoformat(row['date']), row['avg_pitch'] or 0.0)
                for row in cursor.fetchall()
            ]

    def delete_session(self, session_id: int) -> bool:
        """Delete a session and all its readings.

        Args:
            session_id: ID of the session to delete.

        Returns:
            True if session was deleted.
        """
        with self.connection() as conn:
            cursor = conn.cursor()
            # Delete readings first
            cursor.execute("DELETE FROM readings WHERE session_id = ?", (session_id,))
            # Then delete session
            cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
            return cursor.rowcount > 0

    def close_session(self, session_id: int) -> Optional[Session]:
        """Close a session (set end time and compute summary).

        Args:
            session_id: ID of the session to close.

        Returns:
            Updated Session object or None if not found.
        """
        session = self.get_session(session_id)
        if session is None:
            return None

        session.end_time = datetime.now()
        readings = self.get_readings_for_session(session_id)

        if readings:
            session.reading_count = len(readings)
            session.avg_median_pitch = sum(r.median_pitch for r in readings) / len(readings)
            session.avg_voicing_rate = sum(r.voicing_rate for r in readings) / len(readings)

        self.update_session(session)
        return session


def get_default_db() -> Database:
    """Get the default database instance.

    Returns:
        Database instance pointing to ~/.fern/fern.db
    """
    db_path = Path.home() / ".fern" / "fern.db"
    return Database(db_path)

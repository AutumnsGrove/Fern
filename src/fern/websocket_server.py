"""WebSocket server for IPC.

Enables real-time communication between Python backend and Hammerspoon GUI layer.
Handles capture status updates, pitch/resonance data streaming, and command dispatch.
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass, asdict
import threading
import os

try:
    import websockets
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False


logger = logging.getLogger(__name__)


@dataclass
class CaptureStatus:
    """Status of an audio capture session."""
    is_capturing: bool = False
    device_name: Optional[str] = None
    sample_rate: int = 44100
    start_time: Optional[str] = None


@dataclass
class AnalysisResult:
    """Analysis result to send to GUI."""
    median_pitch: float = 0.0
    mean_pitch: float = 0.0
    f1_mean: float = 0.0
    f2_mean: float = 0.0
    f3_mean: float = 0.0
    in_range: bool = False
    deviation: float = 0.0
    timestamp: Optional[str] = None


class WebSocketServer:
    """WebSocket server for Fern IPC."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 8765,
        signal_file: Optional[Path] = None
    ):
        """Initialize the WebSocket server.

        Args:
            host: Host to bind to
            port: Port to listen on
            signal_file: Optional path for signal file communication
        """
        self.host = host
        self.port = port
        self.signal_file = signal_file
        self._server: Optional[asyncio.Server] = None
        self._clients: set = set()
        self._capture_status = CaptureStatus()
        self._analysis_callback: Optional[Callable[[AnalysisResult], None]] = None
        self._running = False

    def set_analysis_callback(self, callback: Callable[[AnalysisResult], None]) -> None:
        """Set callback for analysis results.

        Args:
            callback: Function to call with analysis results.
        """
        self._analysis_callback = callback

    def _update_signal_file(self) -> None:
        """Update signal file with current capture status."""
        if self.signal_file:
            try:
                status_data = {
                    "is_capturing": self._capture_status.is_capturing,
                    "device_name": self._capture_status.device_name,
                    "timestamp": self._capture_status.start_time
                }
                self.signal_file.parent.mkdir(parents=True, exist_ok=True)
                self.signal_file.write_text(json.dumps(status_data))
            except Exception as e:
                logger.warning(f"Failed to update signal file: {e}")

    async def _handle_client(self, websocket):
        """Handle a connected client."""
        client_id = id(websocket)
        self._clients.add(websocket)
        logger.info(f"Client connected: {client_id}")

        try:
            async for message in websocket:
                await self._process_message(websocket, message)
        except Exception as e:
            logger.debug(f"Client error: {e}")
        finally:
            self._clients.discard(websocket)
            logger.info(f"Client disconnected: {client_id}")

    async def _process_message(self, websocket, message: str) -> None:
        """Process incoming message from client."""
        try:
            data = json.loads(message)
            command = data.get("command")

            if command == "status":
                await self._send_status(websocket)
            elif command == "start_capture":
                await self._handle_start_capture(data)
            elif command == "stop_capture":
                await self._handle_stop_capture()
            elif command == "get_targets":
                await self._send_targets(websocket)
            elif command == "ping":
                await websocket.send(json.dumps({"type": "pong"}))
        except json.JSONDecodeError:
            await websocket.send(json.dumps({"type": "error", "message": "Invalid JSON"}))
        except Exception as e:
            await websocket.send(json.dumps({"type": "error", "message": str(e)}))

    async def _send_status(self, websocket) -> None:
        """Send current status to client."""
        await websocket.send(json.dumps({
            "type": "status",
            "data": asdict(self._capture_status)
        }))

    async def _handle_start_capture(self, data: Dict[str, Any]) -> None:
        """Handle start capture command."""
        self._capture_status = CaptureStatus(
            is_capturing=True,
            device_name=data.get("device_name"),
            sample_rate=data.get("sample_rate", 44100)
        )
        self._update_signal_file()
        await self._broadcast_status()

    async def _handle_stop_capture(self) -> None:
        """Handle stop capture command."""
        self._capture_status = CaptureStatus()
        self._update_signal_file()
        await self._broadcast_status()

    async def _send_targets(self, websocket) -> None:
        """Send available targets to client."""
        try:
            from .db import get_default_db
            db = get_default_db()
            targets = db.list_targets()
            targets_data = [
                {
                    "id": t.id,
                    "name": t.name,
                    "min_pitch": t.min_pitch,
                    "max_pitch": t.max_pitch,
                    "is_active": t.is_active
                }
                for t in targets
            ]
            await websocket.send(json.dumps({"type": "targets", "data": targets_data}))
        except Exception as e:
            await websocket.send(json.dumps({"type": "error", "message": str(e)}))

    async def _broadcast_status(self) -> None:
        """Broadcast status to all connected clients."""
        if not self._clients:
            return

        message = json.dumps({
            "type": "status",
            "data": asdict(self._capture_status)
        })

        # Send to all clients concurrently
        await asyncio.gather(
            *(client.send(message) for client in self._clients),
            return_exceptions=True
        )

    async def broadcast_analysis(self, result: AnalysisResult) -> None:
        """Broadcast analysis result to all connected clients.

        Args:
            result: Analysis result to broadcast.
        """
        if not self._clients:
            return

        message = json.dumps({
            "type": "analysis",
            "data": asdict(result)
        })

        await asyncio.gather(
            *(client.send(message) for client in self._clients),
            return_exceptions=True
        )

    async def start(self) -> None:
        """Start the WebSocket server."""
        if not WEBSOCKETS_AVAILABLE:
            logger.warning("websockets library not available, using fallback")
            self._running = True
            return

        self._server = await websockets.serve(
            self._handle_client,
            self.host,
            self.port
        )
        self._running = True
        logger.info(f"WebSocket server started on ws://{self.host}:{self.port}")

    async def stop(self) -> None:
        """Stop the WebSocket server."""
        self._running = False
        if self._server:
            self._server.close()
            await self._server.wait_closed()
            self._server = None
        logger.info("WebSocket server stopped")

    def is_running(self) -> bool:
        """Check if server is running."""
        return self._running

    @property
    def is_capturing(self) -> bool:
        """Check if capture is active."""
        return self._capture_status.is_capturing


class SignalFileManager:
    """Manages signal files for simple IPC with Hammerspoon."""

    CAPTURE_ACTIVE_FILE = Path("/tmp/fern_capture_active")
    RESULTS_FILE = Path("/tmp/fern_results")

    def __init__(self, base_dir: Optional[Path] = None):
        """Initialize signal file manager.

        Args:
            base_dir: Base directory for signal files.
        """
        self.base_dir = base_dir or Path("/tmp")
        self.CAPTURE_ACTIVE_FILE = self.base_dir / "fern_capture_active"
        self.RESULTS_FILE = self.base_dir / "fern_results"

    def set_capture_active(self, active: bool, metadata: Optional[Dict] = None) -> None:
        """Set capture active signal.

        Args:
            active: Whether capture is active.
            metadata: Optional metadata to include.
        """
        if active:
            data = {
                "active": True,
                "timestamp": str(datetime.now().isoformat())
            }
            if metadata:
                data.update(metadata)
            self.CAPTURE_ACTIVE_FILE.parent.mkdir(parents=True, exist_ok=True)
            self.CAPTURE_ACTIVE_FILE.write_text(json.dumps(data))
        else:
            self.CAPTURE_ACTIVE_FILE.unlink(missing_ok=True)

    def is_capture_active(self) -> bool:
        """Check if capture is active."""
        return self.CAPTURE_ACTIVE_FILE.exists()

    def write_result(self, result: AnalysisResult) -> None:
        """Write analysis result to signal file.

        Args:
            result: Analysis result to write.
        """
        self.RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
        self.RESULTS_FILE.write_text(json.dumps(asdict(result)))

    def read_result(self) -> Optional[AnalysisResult]:
        """Read latest analysis result."""
        if not self.RESULTS_FILE.exists():
            return None

        try:
            data = json.loads(self.RESULTS_FILE.read_text())
            return AnalysisResult(**data)
        except Exception:
            return None

    def clear_result(self) -> None:
        """Clear results file."""
        self.RESULTS_FILE.unlink(missing_ok=True)


from datetime import datetime


def get_default_server() -> WebSocketServer:
    """Get default WebSocket server instance.

    Returns:
        Configured WebSocketServer instance.
    """
    return WebSocketServer(signal_file=Path("/tmp/fern_status"))


def get_signal_manager() -> SignalFileManager:
    """Get default signal file manager.

    Returns:
        Configured SignalFileManager instance.
    """
    return SignalFileManager()

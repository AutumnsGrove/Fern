"""""CLI entry point.

Typer-based command line interface for Fern.
Features comprehensive error handling with unique error codes.
"""

from typing import Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.align import Align
from rich.box import ROUNDED
from rich import print as rprint
from datetime import datetime
import csv
import json
import os

from .errors import (
    FernError,
    create_error,
    wrap_exception,
    display_error,
    display_fatal_error,
    ErrorSeverity,
    ErrorCategory,
    handle_errors
)
from .logging import get_logger, log_session, log_capture, log_analysis

app = typer.Typer(
    name="fern",
    help="Voice training feedback companion",
    rich_markup_mode="rich"
)

console = Console()

# Initialize logger
logger = get_logger()


def _fern_exit(code: str = "FERN-000", message: Optional[str] = None) -> None:
    """Exit with a Fern error code.

    Args:
        code: Error code
        message: Optional message override
    """
    error = create_error(code, message=message)
    display_fatal_error(error)


def _display_pitch_result(pitch_result: dict, active_target=None) -> None:
    """Display pitch analysis result with Rich formatting."""
    median_pitch = pitch_result.get('median_pitch', 0)

    # Determine status based on target
    status = "neutral"
    status_icon = "○"
    if active_target and median_pitch > 0:
        if active_target.min_pitch <= median_pitch <= active_target.max_pitch:
            status = "success"
            status_icon = "✓"
        else:
            status = "warning"
            status_icon = "△"

    # Color based on status
    color_map = {
        "success": "green",
        "warning": "yellow",
        "neutral": "blue"
    }
    color = color_map.get(status, "blue")

    # Create result panel
    result_panel = Panel(
        f"[bold {color}]{median_pitch:.1f} Hz[/bold {color}]\n"
        f"[dim]Mean: {pitch_result.get('mean_pitch', 0):.1f} Hz[/dim]\n"
        f"[dim]Range: {pitch_result.get('min_pitch', 0):.0f} - {pitch_result.get('max_pitch', 0):.0f} Hz[/dim]\n"
        f"\n[dim]Voicing: {pitch_result.get('voicing_rate', 0)*100:.1f}%[/dim]",
        title=f" {status_icon} Result ",
        border_style=color,
        box=ROUNDED
    )
    console.print(result_panel)

    # Show target comparison if available
    if active_target:
        in_range = active_target.min_pitch <= median_pitch <= active_target.max_pitch
        target_text = f"Target: {active_target.min_pitch:.0f} - {active_target.max_pitch:.0f} Hz"
        if in_range:
            console.print(f"[green]✓ {target_text}[/green]")
        else:
            deviation = median_pitch - (active_target.min_pitch + active_target.max_pitch) / 2
            direction = "above" if deviation > 0 else "below"
            console.print(f"[yellow]○ {target_text} ({abs(deviation):.0f} Hz {direction})[/yellow]")


def _get_sparkline(values: list, max_width: int = 20) -> str:
    """Create a simple ASCII sparkline for pitch values."""
    if not values or len(values) < 2:
        return ""

    # Normalize values
    min_val = min(values)
    max_val = max(values)
    range_val = max_val - min_val
    if range_val == 0:
        range_val = 1

    # Characters for different heights
    chars = "▁▂▃▄▅▆▇█"

    spark = ""
    for v in values:
        normalized = (v - min_val) / range_val
        char_idx = int(normalized * (len(chars) - 1))
        spark += chars[char_idx]

    return spark


def _format_duration(seconds: float) -> str:
    """Format duration in human-readable format."""
    if seconds < 60:
        return f"{seconds:.0f}s"
    elif seconds < 3600:
        return f"{seconds/60:.1f}m"
    else:
        return f"{seconds/3600:.1f}h"


@app.command()
def status():
    """Show current Fern status."""
    from .db import get_default_db
    from .config import get_default_config, load_config, get_default_config_path, ConfigFileNotFoundError

    console.print(Panel.fit(
        "[bold green]🌿 Fern[/bold green]\n"
        "[dim]Voice training feedback companion[/dim]",
        title="Status",
        border_style="green",
        box=ROUNDED
    ))

    # Check directories
    from pathlib import Path
    data_dir = Path.home() / ".fern"
    clips_dir = data_dir / "clips"
    db_path = data_dir / "fern.db"

    console.print("\n[bold]Directories[/bold]")
    if data_dir.exists():
        console.print(f"  [green]✓[/green] Data: {data_dir}")
        try:
            if db_path.exists():
                db_size = db_path.stat().st_size / 1024
                console.print(f"    [dim]Database: {db_size:.1f} KB[/dim]")
        except OSError as e:
            logger.warning("Could not stat database file", error=str(e))
    else:
        console.print(f"  [yellow]○[/yellow] Data: {data_dir} (not created)")

    if clips_dir.exists():
        clip_count = len(list(clips_dir.glob("**/*.wav")))
        console.print(f"  [green]✓[/green] Clips: {clips_dir} ({clip_count} files)")
    else:
        console.print(f"  [yellow]○[/yellow] Clips: {clips_dir} (not created)")

    # Load config and show target
    try:
        config = load_config(get_default_config_path())
        target = config.get('target', {})
        if target:
            console.print(f"\n[bold]Active Target[/bold]")
            console.print(f"  [green]✓[/green] {target.get('min_pitch', 80)} - {target.get('max_pitch', 250)} Hz")
    except (FileNotFoundError, ConfigFileNotFoundError):
        console.print(f"\n[bold]Active Target[/bold]")
        console.print(f"  [yellow]○[/yellow] Using defaults (80 - 250 Hz)")
    except Exception as e:
        logger.warning("Could not load config", error=str(e))

    # Database stats
    try:
        db = get_default_db()
        sessions = db.list_sessions(limit=1)
        readings = db.get_recent_readings(limit=100)

        console.print(f"\n[bold]Statistics[/bold]")
        console.print(f"  Total sessions: [cyan]{len(sessions)}[/cyan]")
        console.print(f"  Recent readings: [cyan]{len(readings)}[/cyan]")
    except Exception as e:
        console.print(f"\n[dim]Database not initialized yet[/dim]")

    console.print("\n[dim]Use 'fern test' to try pitch detection[/dim]")


@app.command()
def test(
    duration: int = typer.Option(5, "--duration", "-d", help="Recording duration in seconds"),
    device: Optional[int] = typer.Option(None, "--device", "-D", help="Audio device ID"),
    save: bool = typer.Option(False, "--save", "-s", help="Save recording to database")
):
    """Test pitch detection with microphone."""
    from .analysis import extract_pitch_from_audio, extract_resonance_from_audio
    from .db import get_default_db
    from .config import load_config, get_default_config_path, ConfigFileNotFoundError
    import sounddevice as sd
    import numpy as np

    console.print(Panel.fit(
        f"[bold blue]Testing Pitch Detection[/bold blue]\n"
        f"[dim]Recording {duration} seconds of audio...[/dim]",
        title="Fern Test",
        border_style="blue",
        box=ROUNDED
    ))

    try:
        # Load config for target
        try:
            config = load_config(get_default_config_path())
            target = config.get('target', {})
            active_target = type('Target', (), {
                'min_pitch': target.get('min_pitch', 80),
                'max_pitch': target.get('max_pitch', 250)
            })()
        except (FileNotFoundError, ConfigFileNotFoundError):
            active_target = type('Target', (), {'min_pitch': 80, 'max_pitch': 250})()
            logger.info("Using default target range (80-250 Hz)")

        # Record audio
        console.print("\n🎤 [cyan]Recording... Speak now![/cyan]")

        try:
            audio_data = sd.rec(
                duration * 44100,
                samplerate=44100,
                channels=1,
                device=device,
                dtype=np.float32
            )
            sd.wait()
            console.print("✓ Recording complete!")
            log_capture("completed", device=str(device) if device else "default", sample_rate=44100)
        except sd.PortAudioError as e:
            if "Device unavailable" in str(e) or "busy" in str(e).lower():
                raise create_error("FERN-102", technical_details=str(e))
            elif "Invalid sample rate" in str(e):
                raise create_error("FERN-104", technical_details=str(e))
            else:
                raise wrap_exception(e, "FERN-103", {"operation": "audio_capture"})

        # Extract pitch
        console.print("🔍 [cyan]Analyzing pitch...[/cyan]")

        try:
            pitch_result = extract_pitch_from_audio(audio_data.flatten(), 44100)
        except Exception as e:
            logger.exception("Pitch extraction failed", exc=e)
            raise wrap_exception(e, "FERN-200")

        # Extract resonance
        try:
            resonance_result = extract_resonance_from_audio(audio_data.flatten(), 44100)
        except Exception as e:
            logger.exception("Resonance extraction failed", exc=e)
            raise wrap_exception(e, "FERN-203")

        # Combine results
        pitch_result.update({k: v for k, v in resonance_result.items() if k.startswith('f')})

        if pitch_result['median_pitch'] > 0:
            _display_pitch_result(pitch_result, active_target)
            log_analysis(-1, pitch_result['median_pitch'],
                        f1=resonance_result.get('f1_mean'),
                        f2=resonance_result.get('f2_mean'),
                        f3=resonance_result.get('f3_mean'))

            # Show resonance if available
            if resonance_result.get('f1_mean', 0) > 0:
                console.print("\n[bold]Resonance[/bold]")
                console.print(f"  F1: [magenta]{resonance_result['f1_mean']:.0f} Hz[/magenta]")
                console.print(f"  F2: [magenta]{resonance_result['f2_mean']:.0f} Hz[/magenta]")
                console.print(f"  F3: [magenta]{resonance_result['f3_mean']:.0f} Hz[/magenta]")
        else:
            console.print("\n[yellow]⚠ No pitch detected in audio[/yellow]")
            console.print("[dim]Try speaking closer to the microphone or increasing volume[/dim]")
            error = create_error("FERN-201")
            display_error(error)
            raise typer.Exit(0)

        # Save to database if requested
        if save:
            try:
                db = get_default_db()
                session = db.create_session(type('Session', (), {
                    'name': f"Test {datetime.now().isoformat()}",
                    'start_time': datetime.now(),
                    'target_id': None,
                    'notes': None
                })())

                reading = type('Reading', (), {
                    'session_id': session,
                    'timestamp': datetime.now(),
                    'median_pitch': pitch_result['median_pitch'],
                    'mean_pitch': pitch_result['mean_pitch'],
                    'min_pitch': pitch_result['min_pitch'],
                    'max_pitch': pitch_result['max_pitch'],
                    'std_pitch': pitch_result['std_pitch'],
                    'voiced_frames': pitch_result['voiced_frames'],
                    'total_frames': pitch_result['total_frames'],
                    'voicing_rate': pitch_result['voicing_rate'],
                    'f1_mean': resonance_result.get('f1_mean', 0),
                    'f2_mean': resonance_result.get('f2_mean', 0),
                    'f3_mean': resonance_result.get('f3_mean', 0),
                    'f1_std': resonance_result.get('f1_std', 0),
                    'f2_std': resonance_result.get('f2_std', 0),
                    'f3_std': resonance_result.get('f3_std', 0),
                    'clip_path': None,
                    'duration_seconds': duration,
                    'device_id': device
                })()

                reading_id = db.create_reading(reading)
                console.print(f"\n[green]✓ Saved as reading #{reading_id}[/green]")
                log_session(session, "completed", duration=duration, readings=1)
            except Exception as e:
                logger.exception("Failed to save reading", exc=e)
                raise wrap_exception(e, "FERN-300", {"operation": "save_reading"})

    except FernError as e:
        if e.severity == ErrorSeverity.WARNING:
            display_error(e)
            raise typer.Exit(0)
        raise
    except typer.Exit:
        raise
    except KeyboardInterrupt:
        console.print("\n[yellow]Recording cancelled[/yellow]")
        raise typer.Exit(0)
    except Exception as e:
        logger.exception("Test command failed", exc=e)
        console.print(f"\n[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def trend(
    days: int = typer.Option(30, "--days", "-d", help="Number of days of history to show"),
    target_id: Optional[int] = typer.Option(None, "--target", "-t", help="Filter by target ID"),
    sparkline: bool = typer.Option(False, "--sparkline", "-s", help="Show ASCII sparkline")
):
    """Show pitch trend over time."""
    from .db import get_default_db

    console.print(Panel.fit(
        f"[bold cyan]📈 Pitch Trends[/bold cyan]\n"
        f"[dim]Last {days} days of voice training[/dim]",
        title="Fern Trend",
        border_style="cyan",
        box=ROUNDED
    ))

    try:
        db = get_default_db()
        trend_data = db.get_trend_data(days=days, target_id=target_id)

        if not trend_data:
            console.print("\n[yellow]No data available. Start training to see trends![/yellow]")
            console.print("[dim]Use 'fern test --save' to record a session[/dim]")
            return

        # Get active target for range comparison
        active_target = db.get_active_target()
        target_min = active_target.min_pitch if active_target else 80
        target_max = active_target.max_pitch if active_target else 250

        # Calculate overall stats
        pitches = [p for _, p in trend_data if p > 0]
        if pitches:
            avg_pitch = sum(pitches) / len(pitches)
            min_pitch = min(pitches)
            max_pitch = max(pitches)
            in_range_count = sum(1 for p in pitches if target_min <= p <= target_max)
            in_range_pct = in_range_count / len(pitches) * 100

            # Calculate trend direction
            trend_icon = "→"
            trend_color = "dim"
            if len(pitches) >= 7:
                recent_week = pitches[-7:]
                earlier_week = pitches[:7] if len(pitches) >= 14 else pitches[:-7]
                if recent_week and earlier_week:
                    recent_avg = sum(recent_week) / len(recent_week)
                    earlier_avg = sum(earlier_week) / len(earlier_week)
                    delta = recent_avg - earlier_avg
                    if delta > 5:
                        trend_icon = "↑"
                        trend_color = "green"
                    elif delta < -5:
                        trend_icon = "↓"
                        trend_color = "red"
                    else:
                        trend_icon = "→"
                        trend_color = "yellow"

            console.print(f"\n[bold]Statistics ({len(pitches)} readings)[/bold]")

            stats_table = Table(show_header=False, box=None)
            stats_table.add_column("Label", style="dim")
            stats_table.add_column("Value", justify="right")

            stats_table.add_row("Average", f"[cyan]{avg_pitch:.1f} Hz[/cyan]")
            stats_table.add_row("Range", f"{min_pitch:.0f} - {max_pitch:.0f} Hz")
            stats_table.add_row("In Target", f"[green]{in_range_pct:.0f}%[/green]")
            stats_table.add_row("Trend", f"[{trend_color}]{trend_icon} {trend_color}[/{trend_color}]")

            console.print(stats_table)

            # Show sparkline if requested
            if sparkline:
                spark = _get_sparkline(pitches[-30:] if len(pitches) > 30 else pitches)
                console.print(f"\n[bold]Sparkline[/bold]")
                console.print(f"[cyan]{spark}[/cyan]")

        # Show recent data table
        console.print(f"\n[bold]Recent Readings[/bold]")
        table = Table(show_header=True, header_style="bold magenta", box=ROUNDED)
        table.add_column("Date", style="dim", width=12)
        table.add_column("Avg Pitch", justify="right", width=12)
        table.add_column("Status", width=14)
        table.add_column("Spark", width=24)

        # Add sparklines to table
        pitches_for_spark = [p for _, p in trend_data if p > 0]

        for i, (date, pitch) in enumerate(trend_data[-14:]):
            date_str = date.strftime("%Y-%m-%d")
            pitch_str = f"[cyan]{pitch:.1f} Hz[/cyan]" if pitch > 0 else "—"

            if pitch > 0:
                if target_min <= pitch <= target_max:
                    status = "[green]✓ In range[/green]"
                else:
                    status = "[yellow]△ Out of range[/yellow]"
            else:
                status = "[dim]—[/dim]"

            # Mini sparkline for this row (last N points up to this point)
            spark_values = [v for _, v in trend_data[max(0, i - len(trend_data) - 20):i + 1] if v > 0]
            spark = _get_sparkline(spark_values) if spark_values else ""

            table.add_row(date_str, pitch_str, status, f"[dim]{spark}[/dim]")

        console.print(Align.center(table))

    except FernError:
        raise
    except Exception as e:
        logger.exception("Trend command failed", exc=e)
        raise wrap_exception(e, "FERN-300", {"operation": "get_trend_data"})


@app.command()
def sessions(
    limit: int = typer.Option(10, "--limit", "-l", help="Maximum sessions to show")
):
    """List recent training sessions."""
    from .db import get_default_db

    console.print(Panel.fit(
        f"[bold purple]📋 Recent Sessions[/bold purple]\n"
        f"[dim]Last {limit} training sessions[/dim]",
        title="Fern Sessions",
        border_style="purple",
        box=ROUNDED
    ))

    try:
        db = get_default_db()
        sessions = db.list_sessions(limit=limit)

        if not sessions:
            console.print("\n[yellow]No sessions recorded yet.[/yellow]")
            console.print("[dim]Use 'fern test --save' to start a session[/dim]")
            return

        table = Table(show_header=True, header_style="bold magenta", box=ROUNDED)
        table.add_column("ID", width=6, justify="right")
        table.add_column("Date", style="dim", width=14)
        table.add_column("Readings", justify="right", width=10)
        table.add_column("Avg Pitch", justify="right", width=12)
        table.add_column("Duration", width=10)

        for session in sessions:
            start_date = session.start_time.strftime("%Y-%m-%d %H:%M")
            readings = str(session.reading_count)
            avg_pitch = f"{session.avg_median_pitch:.1f} Hz" if session.avg_median_pitch > 0 else "—"

            # Calculate duration if end_time available
            if session.end_time:
                duration = (session.end_time - session.start_time).total_seconds()
                duration_str = _format_duration(duration)
            else:
                duration_str = "—"

            table.add_row(
                str(session.id or "—"),
                start_date,
                readings,
                avg_pitch,
                duration_str
            )

        console.print(Align.center(table))

    except FernError:
        raise
    except Exception as e:
        logger.exception("Sessions command failed", exc=e)
        raise wrap_exception(e, "FERN-300", {"operation": "list_sessions"})


@app.command()
def review(
    session_id: int,
    export: Optional[str] = typer.Option(None, "--export", "-e", help="Export format: csv, json")
):
    """Review a specific session in detail."""
    from .db import get_default_db

    console.print(Panel.fit(
        f"[bold magenta]📖 Session #{session_id}[/bold magenta]",
        title="Fern Review",
        border_style="magenta",
        box=ROUNDED
    ))

    try:
        db = get_default_db()
        session = db.get_session(session_id)

        if not session:
            raise create_error("FERN-503", context={"session_id": session_id})

        readings = db.get_readings_for_session(session_id)

        # Session summary
        console.print(f"\n[bold]Session Info[/bold]")
        console.print(f"  Date: {session.start_time.strftime('%Y-%m-%d %H:%M')}")
        if session.end_time:
            duration = (session.end_time - session.start_time).total_seconds()
            console.print(f"  Duration: {_format_duration(duration)}")
        console.print(f"  Readings: {len(readings)}")

        if session.avg_median_pitch > 0:
            console.print(f"  Average Pitch: [cyan]{session.avg_median_pitch:.1f} Hz[/cyan]")

        if session.notes:
            console.print(f"\n[bold]Notes[/bold]")
            console.print(f"  [dim]{session.notes}[/dim]")

        if not readings:
            console.print("\n[yellow]No readings in this session[/yellow]")
            return

        # Readings table
        console.print(f"\n[bold]Readings[/bold]")
        table = Table(show_header=True, header_style="bold cyan", box=ROUNDED)
        table.add_column("Time", style="dim", width=10)
        table.add_column("Pitch", justify="right", width=10)
        table.add_column("Mean", justify="right", width=10)
        table.add_column("Voicing", justify="right", width=10)
        table.add_column("F1", justify="right", width=8)
        table.add_column("F2", justify="right", width=8)

        for reading in readings:
            time_str = reading.timestamp.strftime("%H:%M")
            pitch = f"{reading.median_pitch:.1f}" if reading.median_pitch > 0 else "—"
            mean = f"{reading.mean_pitch:.1f}" if reading.mean_pitch > 0 else "—"
            voicing = f"{reading.voicing_rate*100:.0f}%" if reading.voicing_rate > 0 else "—"
            f1 = f"{reading.f1_mean:.0f}" if reading.f1_mean > 0 else "—"
            f2 = f"{reading.f2_mean:.0f}" if reading.f2_mean > 0 else "—"

            table.add_row(time_str, pitch, mean, voicing, f1, f2)

        console.print(Align.center(table))

        # Export if requested
        if export:
            if export == "csv":
                csv_path = f"session_{session_id}.csv"
                with open(csv_path, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=[
                        'id', 'timestamp', 'median_pitch', 'mean_pitch', 'min_pitch',
                        'max_pitch', 'voicing_rate', 'f1_mean', 'f2_mean', 'f3_mean'
                    ])
                    writer.writeheader()
                    for r in readings:
                        writer.writerow(r.to_dict())
                console.print(f"\n[green]✓ Exported to {csv_path}[/green]")

            elif export == "json":
                json_path = f"session_{session_id}.json"
                with open(json_path, 'w') as f:
                    json.dump({
                        'session': session.to_dict(),
                        'readings': [r.to_dict() for r in readings]
                    }, f, indent=2)
                console.print(f"\n[green]✓ Exported to {json_path}[/green]")

            else:
                raise create_error("FERN-504", context={"format": export})

    except FernError:
        raise
    except Exception as e:
        logger.exception("Review command failed", exc=e)
        raise wrap_exception(e, "FERN-300", {"operation": "get_session", "session_id": session_id})


@app.command()
def export(
    format: str = typer.Option("csv", "--format", "-f", help="Export format: csv, json"),
    days: int = typer.Option(30, "--days", "-d", help="Export data from last N days"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path")
):
    """Export training data."""
    from .db import get_default_db
    from datetime import timedelta

    format_map = {"csv": "CSV", "json": "JSON"}
    format_name = format_map.get(format, format.upper())

    # Validate format
    if format not in ("csv", "json"):
        raise create_error("FERN-504", context={"format": format})

    console.print(Panel.fit(
        f"[bold green]📤 Export Data[/bold green]\n"
        f"[dim]Last {days} days as {format_name}[/dim]",
        title="Fern Export",
        border_style="green",
        box=ROUNDED
    ))

    try:
        db = get_default_db()
        cutoff = datetime.now() - timedelta(days=days)
        readings = db.get_recent_readings(1000)

        # Filter by date
        filtered_readings = [r for r in readings if r.timestamp >= cutoff]

        if not filtered_readings:
            console.print("\n[yellow]No data to export[/yellow]")
            return

        # Determine output path
        if output:
            output_path = output
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"fern_export_{timestamp}.{format}"

        if format == "csv":
            with open(output_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'id', 'session_id', 'timestamp', 'median_pitch', 'mean_pitch',
                    'min_pitch', 'max_pitch', 'voicing_rate', 'f1_mean', 'f2_mean', 'f3_mean'
                ])
                writer.writeheader()
                for r in filtered_readings:
                    writer.writerow(r.to_dict())

        elif format == "json":
            with open(output_path, 'w') as f:
                json.dump({
                    'export_date': datetime.now().isoformat(),
                    'days': days,
                    'total_readings': len(filtered_readings),
                    'readings': [r.to_dict() for r in filtered_readings]
                }, f, indent=2)

        console.print(f"\n[green]✓ Exported {len(filtered_readings)} readings to {output_path}[/green]")

    except FernError:
        raise
    except PermissionError as e:
        raise wrap_exception(e, "FERN-505", {"path": output_path, "operation": "write"})
    except OSError as e:
        raise wrap_exception(e, "FERN-505", {"path": output_path, "operation": "write"})
    except Exception as e:
        logger.exception("Export command failed", exc=e)
        raise wrap_exception(e, "FERN-300", {"operation": "export"})


@app.command()
def version():
    """Show Fern version."""
    from . import __version__
    from rich.text import Text

    version_text = Text()
    version_text.append("🌿 Fern v", style="green")
    version_text.append(__version__, style="bold cyan")
    version_text.append("\nVoice training feedback companion", style="dim")

    console.print(Panel(version_text, title="Version", border_style="green", box=ROUNDED))


@app.command()
def config():
    """Configure Fern settings."""
    console.print(Panel.fit(
        "[bold yellow]⚙️ Fern Configuration[/bold yellow]",
        title="Config",
        border_style="yellow",
        box=ROUNDED
    ))
    console.print("Use subcommands: [cyan]set-target[/cyan], [cyan]show[/cyan]")
    console.print("Example: [dim]fern config set-target 100 200[/dim]")


@app.command("config:show")
def config_show():
    """Show current configuration."""
    from .config import load_config, get_default_config_path
    from .db import get_default_db

    console.print(Panel.fit(
        "[bold blue]⚙️ Current Configuration[/bold blue]",
        title="Config",
        border_style="blue",
        box=ROUNDED
    ))

    try:
        config = load_config(get_default_config_path())
        target = config.get("target_pitch_range", {})
        audio = config.get("audio", {})
        analysis = config.get("analysis", {})

        console.print("\n[bold]Target Pitch Range[/bold]")
        console.print(f"  Min: [cyan]{target.get('min', 80):.0f} Hz[/cyan]")
        console.print(f"  Max: [cyan]{target.get('max', 250):.0f} Hz[/cyan]")

        console.print("\n[bold]Audio Settings[/bold]")
        console.print(f"  Sample Rate: [cyan]{audio.get('sample_rate', 44100)} Hz[/cyan]")
        console.print(f"  Channels: [cyan]{audio.get('channels', 1)}[/cyan]")
        if audio.get('device'):
            console.print(f"  Device ID: [cyan]{audio.get('device')}[/cyan]")

        console.print("\n[bold]Analysis Settings[/bold]")
        console.print(f"  Pitch Min: [cyan]{analysis.get('pitch_min', 75)} Hz[/cyan]")
        console.print(f"  Pitch Max: [cyan]{analysis.get('pitch_max', 600)} Hz[/cyan]")

        # Also show active database target
        try:
            db = get_default_db()
            active_target = db.get_active_target()
            if active_target:
                console.print("\n[bold]Database Target[/bold]")
                console.print(f"  Name: [cyan]{active_target.name}[/cyan]")
                console.print(f"  Range: [cyan]{active_target.min_pitch:.0f} - {active_target.max_pitch:.0f} Hz[/cyan]")
        except Exception:
            pass

    except FileNotFoundError:
        raise create_error("FERN-400")
    except Exception as e:
        logger.exception("Config show failed", exc=e)
        raise wrap_exception(e, "FERN-401", {"operation": "load_config"})


@app.command("config:set-target")
def config_set_target(
    min_pitch: float = typer.Argument(..., help="Minimum target pitch in Hz"),
    max_pitch: float = typer.Argument(..., help="Maximum target pitch in Hz"),
    update_db: bool = typer.Option(False, "--db", help="Also update database target")
):
    """Set the target pitch range."""
    from .config import load_config, save_config, get_default_config_path, set_target, get_default_config
    from .db import get_default_db, Target

    console.print(Panel.fit(
        f"[bold green]🎯 Set Target Range[/bold green]\n"
        f"[dim]{min_pitch:.0f} - {max_pitch:.0f} Hz[/dim]",
        title="Config",
        border_style="green",
        box=ROUNDED
    ))

    try:
        # Validate pitch range
        if min_pitch >= max_pitch:
            raise create_error("FERN-403", context={"min_pitch": min_pitch, "max_pitch": max_pitch})

        # Load existing config or create new one
        try:
            config = load_config(get_default_config_path())
        except Exception:
            config = get_default_config()
            console.print("[dim]Created new configuration file[/dim]")

        # Validate and set target
        config = set_target(config, min_pitch, max_pitch)
        save_config(config, get_default_config_path())
        console.print(f"\n[green]✓ Target range set to {min_pitch:.0f} - {max_pitch:.0f} Hz[/green]")

        # Also update database if requested
        if update_db:
            db = get_default_db()
            target = Target(
                name=f"CLI Target {datetime.now().strftime('%Y-%m-%d')}",
                min_pitch=min_pitch,
                max_pitch=max_pitch,
                is_active=True
            )
            target_id = db.create_target(target)
            db.set_active_target(target_id)
            console.print(f"[green]✓ Also updated database target (ID: {target_id})[/green]")

    except FernError:
        raise
    except PermissionError as e:
        raise wrap_exception(e, "FERN-003", {"path": str(get_default_config_path()), "operation": "write"})
    except Exception as e:
        logger.exception("Config set-target failed", exc=e)
        raise wrap_exception(e, "FERN-402", {"operation": "save_config"})


@app.command()
def chart(
    days: int = typer.Option(7, "--days", "-d", help="Number of days of data to show"),
    send: bool = typer.Option(False, "--send", "-s", help="Send data to Hammerspoon GUI"),
    view: str = typer.Option("trend", "--view", "-v", help="View: trend, resonance, summary")
):
    """Show pitch charts and optionally send data to Hammerspoon GUI."""
    from .db import get_default_db
    from datetime import timedelta
    from pathlib import Path

    console.print(Panel.fit(
        f"[bold green]📊 Fern Chart Data[/bold green]\n"
        f"[dim]Last {days} days[/dim]",
        title="Charts",
        border_style="green",
        box=ROUNDED
    ))

    try:
        db = get_default_db()
        cutoff = datetime.now() - timedelta(days=days)
        readings = db.get_recent_readings(1000)
        filtered_readings = [r for r in readings if r.timestamp >= cutoff]

        if not filtered_readings:
            console.print("\n[yellow]No data available for the selected period[/yellow]")
            console.print("[dim]Capture some audio first with 'fern test --save'[/dim]")
            raise create_error("FERN-303")

        # Group readings by date for trend data
        trend_by_date = {}
        session_stats = {}
        total_pitch = 0
        in_range_count = 0

        # Get target range
        try:
            active_target = db.get_active_target()
            target_min = active_target.min_pitch if active_target else 80
            target_max = active_target.max_pitch if active_target else 250
        except Exception:
            target_min = 80
            target_max = 250

        for r in filtered_readings:
            if r.median_pitch > 0:
                date_key = r.timestamp.strftime("%Y-%m-%d")
                if date_key not in trend_by_date:
                    trend_by_date[date_key] = []
                trend_by_date[date_key].append(r.median_pitch)

                total_pitch += r.median_pitch

                if target_min <= r.median_pitch <= target_max:
                    in_range_count += 1

        # Build trend data
        trend_data = []
        for date in sorted(trend_by_date.keys()):
            values = trend_by_date[date]
            avg_pitch = sum(values) / len(values)
            trend_data.append({
                "date": date,
                "value": avg_pitch
            })

        # Calculate stats
        num_readings = len([r for r in filtered_readings if r.median_pitch > 0])
        avg_pitch = total_pitch / num_readings if num_readings > 0 else 0
        in_range_pct = (in_range_count / num_readings * 100) if num_readings > 0 else 0

        # Get recent sessions for summary
        sessions = db.list_sessions(limit=10)
        session_list = []
        for s in sessions:
            s_readings = db.get_readings_for_session(s.id)
            s_pitch_values = [r.median_pitch for r in s_readings if r.median_pitch > 0]
            s_avg = sum(s_pitch_values) / len(s_pitch_values) if s_pitch_values else 0
            s_in_range = sum(1 for p in s_pitch_values if target_min <= p <= target_max)
            s_pct = (s_in_range / len(s_pitch_values) * 100) if s_pitch_values else 0

            session_list.append({
                "date": s.timestamp.strftime("%Y-%m-%d %H:%M"),
                "duration": f"{s.duration_s:.0f}s",
                "avgPitch": f"{s_avg:.0f} Hz",
                "inRange": s_pct >= 50
            })

        # Prepare chart data
        chart_data = {
            "trend": trend_data,
            "resonance": {
                "f1": 0,
                "f2": 0,
                "f3": 0
            },
            "stats": {
                "sessions": len(sessions),
                "totalTime": f"{sum(s.duration_s for s in sessions):.0f}m",
                "avgPitch": avg_pitch,
                "inRangePct": in_range_pct,
                "bestDay": max(trend_by_date.keys(), key=lambda d: sum(trend_by_date[d])/len(trend_by_date[d]) if trend_by_date[d] else 0) if trend_by_date else "--",
                "streak": 0
            },
            "sessions": session_list,
            "targetMin": target_min,
            "targetMax": target_max
        }

        # Display summary
        console.print(f"\n[bold]Period Summary ({days} days)[/bold]")
        console.print(f"  Sessions: [cyan]{len(sessions)}[/cyan]")
        console.print(f"  Total readings: [cyan]{num_readings}[/cyan]")
        console.print(f"  Average pitch: [cyan]{avg_pitch:.0f} Hz[/cyan]")
        console.print(f"  In range: [cyan]{in_range_pct:.0f}%[/cyan]")
        console.print(f"  Target: [cyan]{target_min:.0f} - {target_max:.0f} Hz[/cyan]")

        # Show sparkline
        if len(trend_data) > 1:
            values = [d["value"] for d in trend_data]
            sparkline = _get_sparkline(values, 30)
            console.print(f"\n[bold]Trend Sparkline[/bold]")
            console.print(f"  [green]{sparkline}[/green]")

        # Send to Hammerspoon if requested
        if send:
            signal_path = Path("/tmp/fern_chart_data")
            signal_path.parent.mkdir(parents=True, exist_ok=True)
            signal_path.write_text(json.dumps(chart_data))
            console.print(f"\n[green]✓ Chart data sent to Hammerspoon[/green]")
            console.print("[dim]Press Ctrl+Alt+Shift+C in Hammerspoon to view charts[/dim]")
        else:
            console.print(f"\n[dim]Use --send flag to send data to Hammerspoon GUI[/dim]")
            console.print("[dim]Press Ctrl+Alt+Shift+C in Hammerspoon to view charts[/dim]")

    except FernError:
        raise
    except Exception as e:
        logger.exception("Chart command failed", exc=e)
        console.print(f"\n[red]Error: {e}[/red]")
        raise typer.Exit(1)


def main():
    """Main entry point with error handling."""
    try:
        app()
    except FernError as e:
        display_fatal_error(e)
    except KeyboardInterrupt:
        raise typer.Exit(0)


if __name__ == "__main__":
    main()

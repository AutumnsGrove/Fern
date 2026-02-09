"""""CLI entry point.

Typer-based command line interface for Fern.
"""

from typing import Optional
import typer
from rich.console import Console
from rich.panel import Panel

app = typer.Typer(
    name="fern",
    help="Voice training feedback companion",
    rich_markup_mode="rich"
)

console = Console()


@app.command()
def status():
    """Show current Fern status."""
    console.print(Panel.fit(
        "[bold green]Fern Voice Training[/bold green]\n"
        "[dim]Voice training feedback companion[/dim]",
        title="Status",
        border_style="green"
    ))
    
    # Check if data directory exists
    import os
    from pathlib import Path
    
    data_dir = Path.home() / ".fern"
    if data_dir.exists():
        console.print(f"✓ Data directory: {data_dir}")
    else:
        console.print(f"○ Data directory: {data_dir} (not created yet)")
    
    console.print("Ready to track your voice training journey!")


@app.command()
def test(
    duration: int = typer.Option(5, "--duration", "-d", help="Recording duration in seconds"),
    device: Optional[int] = typer.Option(None, "--device", "-D", help="Audio device ID")
):
    """Test pitch detection with microphone."""
    from .analysis import extract_pitch_from_audio
    import sounddevice as sd
    import numpy as np
    
    console.print(Panel.fit(
        f"[bold blue]Testing Pitch Detection[/bold blue]\n"
        f"[dim]Recording {duration} seconds of audio...[/dim]",
        title="Fern Test",
        border_style="blue"
    ))
    
    try:
        # Record audio
        console.print("🎤 Recording audio... Speak now!")
        audio_data = sd.rec(
            duration * 44100, 
            samplerate=44100, 
            channels=1,
            device=device,
            dtype=np.float32
        )
        sd.wait()
        console.print("✓ Recording complete!")
        
        # Extract pitch
        console.print("🔍 Analyzing pitch...")
        pitch_result = extract_pitch_from_audio(audio_data.flatten(), 44100)
        
        if pitch_result['median_pitch'] > 0:
            console.print(f"✓ Median pitch: [bold]{pitch_result['median_pitch']:.1f} Hz[/bold]")
        else:
            console.print("⚠ No pitch detected in audio")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def trend(
    days: int = typer.Option(30, "--days", "-d", help="Number of days of history to show"),
    target_id: Optional[int] = typer.Option(None, "--target", "-t", help="Filter by target ID")
):
    """Show pitch trend over time."""
    from .db import get_default_db
    from rich.table import Table
    from rich.align import Align
    from datetime import datetime, timedelta

    console.print(Panel.fit(
        f"[bold cyan]Pitch Trends[/bold cyan]\n"
        f"[dim]Last {days} days of voice training[/dim]",
        title="Fern Trend",
        border_style="cyan"
    ))

    try:
        db = get_default_db()
        trend_data = db.get_trend_data(days=days, target_id=target_id)

        if not trend_data:
            console.print("[yellow]No data available. Start training to see trends![/yellow]")
            return

        # Calculate overall stats
        pitches = [p for _, p in trend_data if p > 0]
        if pitches:
            avg_pitch = sum(pitches) / len(pitches)
            min_pitch = min(pitches)
            max_pitch = max(pitches)

            # Calculate trend direction
            if len(pitches) >= 7:
                recent_week = pitches[-7:]
                earlier_week = pitches[:7] if len(pitches) >= 14 else pitches[:-7]
                if recent_week and earlier_week:
                    recent_avg = sum(recent_week) / len(recent_week)
                    earlier_avg = sum(earlier_week) / len(earlier_week)
                    delta = recent_avg - earlier_avg
                    if delta > 5:
                        trend = "[green]↑ Rising[/green]"
                    elif delta < -5:
                        trend = "[red]↓ Falling[/red]"
                    else:
                        trend = "[yellow]→ Stable[/yellow]"
                else:
                    trend = "[dim]→ Stable[/dim]"
            else:
                trend = "[dim]→ Need more data[/dim]"

            console.print(f"\n[bold]Overall Statistics:[/bold]")
            console.print(f"  Average: [cyan]{avg_pitch:.1f} Hz[/cyan]")
            console.print(f"  Range:   {min_pitch:.1f} - {max_pitch:.1f} Hz")
            console.print(f"  Trend:   {trend}")

        # Show recent data table
        console.print(f"\n[bold]Recent Readings:[/bold]")
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Date", style="dim", width=12)
        table.add_column("Avg Pitch", justify="right")
        table.add_column("Status", width=10)

        # Get active target for range comparison
        active_target = db.get_active_target()
        target_min = active_target.min_pitch if active_target else 80
        target_max = active_target.max_pitch if active_target else 250

        for date, pitch in trend_data[-14:]:  # Show last 14 entries max
            date_str = date.strftime("%Y-%m-%d")
            pitch_str = f"{pitch:.1f} Hz" if pitch > 0 else "—"

            if pitch > 0:
                if target_min <= pitch <= target_max:
                    status = "[green]✓ In range[/green]"
                else:
                    status = "[yellow]○ Out of range[/yellow]"
            else:
                status = "[dim]—[/dim]"

            table.add_row(date_str, pitch_str, status)

        console.print(Align.center(table))

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def version():
    """Show Fern version."""
    from . import __version__
    console.print(f"Fern v{__version__}")


if __name__ == "__main__":
    app()

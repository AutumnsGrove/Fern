# Fern — Voice Training Feedback Companion

*A complete technical specification for the Grove ecosystem*

---

---
aliases: []
date created: Tuesday, February 4th 2026
date modified: Tuesday, February 4th 2026
tags:
  - voice-training
  - personal-tools
  - python
  - hammerspoon
  - accessibility
type: tech-spec
---

# Fern — Voice Training Feedback Companion

```
                    🌿

              \     |     /
               \    |    /
                \   |   /
                 \  |  /
                    |
               ╭────┴────╮
               │  ● │ ●  │
               │pitch res│
               ╰────┬────╯
                    │
                ════╧════
               ╱╱╱╱╱╱╱╱╱╱╱
              ───────────────
             ~ voice becomes ~
             ~    visible    ~

        Gentle feedback, constant growth.
        Every word is practice.
```

> *Gentle feedback, constant growth. Every word is practice.*

Fern is a voice training feedback companion that hooks into your existing dictation workflow. It listens when you speak, shows you what your voice is doing, and helps you grow toward the voice you want. No dedicated practice sessions required. The friction is built into something you're already doing.

**Public Name:** Fern
**Internal Name:** Fern (standalone tool, Grove-adjacent)
**Repository:** `github.com/autumnsgrove/fern`
**Status:** Planned
**Last Updated:** February 2026

In the forest, ferns unfurl slowly. They don't rush. They grow in the shade, patient, persistent. Each frond a little different from the last, but all part of the same plant reaching toward light.

Voice training is like that. You don't wake up one day with a new voice. You unfurl. Word by word, day by day, you grow toward the voice that was always yours.

Fern is the companion that sits with you while you unfurl.

---

## Overview

### The Problem

Voice training requires consistent practice and feedback. But dedicated practice sessions are hard to maintain. They feel like homework. They require carving out time. They require *wanting* to hear yourself, which is often the hardest part.

Meanwhile, you're already recording yourself constantly. Every time you use Hex to dictate, you're speaking. That audio exists. It could be teaching you something.

### The Solution

Fern attaches to your existing dictation workflow. Same hotkey as Hex. When you hold it down to dictate, Fern listens too. It shows you two simple indicators: where your pitch is, where your resonance is. When you release, it shows a brief summary chart, logs the data, and gets out of your way.

You don't "do voice training." You just dictate. And slowly, you learn to hear yourself. You start noticing patterns. You adjust. You grow.

### Goals

1. **Zero additional friction** — uses the same hotkey as your existing workflow
2. **Passive feedback** — you don't study the data, you absorb it peripherally
3. **Long-term visibility** — quarterly snapshots let you see growth over months
4. **Playback on demand** — hear yourself when you're ready, not before
5. **Guided exercises** — structured practice when you want more (v1.5)

### Non-Goals

- Replacing dedicated voice coaching
- Providing medical or clinical analysis
- Achieving "perfect" pitch/resonance detection
- Looking pretty (function over form, beauty comes through iteration)

---

## Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                              USER                                   │
│                                                                     │
│                    [Holds Right Option key]                         │
│                              │                                      │
│              ┌───────────────┴───────────────┐                      │
│              ▼                               ▼                      │
│     ┌─────────────────┐             ┌─────────────────┐             │
│     │       Hex       │             │    Hammerspoon  │             │
│     │  (transcription)│             │   (Fern GUI)    │             │
│     └────────┬────────┘             └────────┬────────┘             │
│              │                               │                      │
│              │                               │ spawns               │
│              │                               ▼                      │
│              │                      ┌─────────────────┐             │
│              │                      │  Python Backend │             │
│              │                      │   (fern-daemon) │             │
│              │                      └────────┬────────┘             │
│              │                               │                      │
│              ▼                               ▼                      │
│     ┌─────────────────┐             ┌─────────────────┐             │
│     │   Transcribed   │             │  Voice Analysis │             │
│     │      Text       │             │    Feedback     │             │
│     └─────────────────┘             └─────────────────┘             │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Component Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         HAMMERSPOON                                 │
│                        (Lua - GUI Layer)                            │
│                                                                     │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐            │
│  │    Hotkey     │  │  Live Overlay │  │    Summary    │            │
│  │   Listener    │  │   (2 dots)    │  │  Chart View   │            │
│  └───────┬───────┘  └───────▲───────┘  └───────▲───────┘            │
│          │                  │                  │                    │
│          │ on key down      │ JSON updates     │ PNG path           │
│          ▼                  │                  │                    │
│  ┌───────────────────────────────────────────────────────┐          │
│  │              Process Manager / IPC Handler            │          │
│  └───────────────────────────┬───────────────────────────┘          │
│                              │                                      │
└──────────────────────────────┼──────────────────────────────────────┘
                               │ spawns process, reads stdout
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         PYTHON BACKEND                              │
│                         (fern package)                              │
│                                                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐  │
│  │  capture.py │  │ analysis.py │  │  charts.py  │  │   db.py    │  │
│  │             │  │             │  │             │  │            │  │
│  │ sounddevice │  │  librosa    │  │ matplotlib  │  │  sqlite3   │  │
│  │ audio input │  │  parselmouth│  │ PNG output  │  │  storage   │  │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └─────┬──────┘  │
│         │                │                │               │         │
│         └────────────────┴────────────────┴───────────────┘         │
│                                   │                                 │
│                    ┌──────────────┴──────────────┐                  │
│                    ▼                             ▼                  │
│           ┌─────────────────┐          ┌─────────────────┐          │
│           │ audio_manager.py│          │    main.py      │          │
│           │                 │          │                 │          │
│           │ rolling clips   │          │ daemon mode     │          │
│           │quarterly archive│          │ CLI interface   │          │
│           └─────────────────┘          └─────────────────┘          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          CLI (fern)                                 │
│                         (Typer-based)                               │
│                                                                     │
│   fern log [recent|stats|progress|search|export]                    │
│   fern audio [list|play|archive|play-archive]                       │
│   fern config [view|set]                                            │
│   fern exercise [list|start|history]  ← v1.5                        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
RECORDING FLOW
══════════════

  ┌─────────┐     ┌─────────────┐     ┌──────────────┐     ┌──────────┐
  │ Hotkey  │────▶│   Audio     │────▶│   Analyze    │────▶│  Stream  │
  │  Down   │     │  Capture    │     │   Chunks     │     │   JSON   │
  └─────────┘     │  (stream)   │     │  (realtime)  │     │  stdout  │
                  └─────────────┘     └──────────────┘     └────┬─────┘
                                                                │
                  ┌─────────────────────────────────────────────┘
                  ▼
           ┌─────────────┐
           │ Hammerspoon │
           │  updates    │
           │  overlay    │
           └─────────────┘


COMPLETION FLOW
═══════════════

  ┌─────────┐     ┌─────────────┐     ┌──────────────┐     ┌──────────┐
  │ Hotkey  │────▶│   Final     │────▶│    Save      │────▶│  Render  │
  │   Up    │     │  Analysis   │     │   to DB      │     │  Chart   │
  └─────────┘     └─────────────┘     └──────────────┘     └────┬─────┘
                                                                │
                        ┌───────────────────────────────────────┤
                        │                                       │
                        ▼                                       ▼
                 ┌─────────────┐                        ┌─────────────┐
                 │  Manage     │                        │  Display    │
                 │  Audio Clip │                        │  Summary    │
                 │  (rolling)  │                        │  (10 sec)   │
                 └─────────────┘                        └─────────────┘
```

---

## Tech Stack

### Python Backend

| Component | Library | Purpose |
|-----------|---------|---------|
| Audio capture | `sounddevice` | Real-time microphone input |
| Pitch detection | `librosa` | Fundamental frequency (f0) extraction |
| Resonance analysis | `praat-parselmouth` | Formant (R1) extraction |
| Array ops | `numpy` | Signal processing |
| Charts | `matplotlib` | Summary chart generation |
| CLI | `typer` + `rich` | Command-line interface |
| Database | `sqlite3` (stdlib) | Metrics storage |
| Config | `tomli` / `tomllib` | Configuration file parsing |
| Audio playback | `sounddevice` or `playsound` | Clip playback |

### GUI Layer

| Component | Tool | Purpose |
|-----------|------|---------|
| Hotkey listener | Hammerspoon | Global hotkey detection |
| Overlay rendering | Hammerspoon canvas | Floating transparent windows |
| Process management | Hammerspoon | Spawning Python, reading stdout |
| Image display | Hammerspoon | Showing chart PNGs |

### System Requirements

- macOS (Hammerspoon is macOS-only)
- Python 3.11+
- Homebrew (for installing dependencies)
- PortAudio (`brew install portaudio`)
- Hammerspoon (`brew install --cask hammerspoon`)

---

## Data Model

### SQLite Schema

```sql
-- ═══════════════════════════════════════════════════════════════════
-- SESSIONS TABLE
-- Core metrics for each recording (kept forever)
-- ═══════════════════════════════════════════════════════════════════

CREATE TABLE sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,              -- ISO 8601 (2026-02-04T14:32:01Z)
    duration_seconds REAL NOT NULL,       -- Length of recording
    
    -- Pitch metrics (Hz)
    pitch_mean_hz REAL,                   -- Average fundamental frequency
    pitch_median_hz REAL,                 -- Median (less affected by outliers)
    pitch_min_hz REAL,                    -- Lowest detected pitch
    pitch_max_hz REAL,                    -- Highest detected pitch
    pitch_std_dev REAL,                   -- Variation (expressiveness indicator)
    pitch_in_target_pct REAL,             -- % of frames in target range
    
    -- Resonance metrics
    resonance_r1_mean_hz REAL,            -- First formant average frequency
    resonance_brightness REAL,            -- Computed 0-100 score
    resonance_in_target_pct REAL,         -- % of frames in target range
    
    -- Audio reference
    audio_clip_path TEXT,                 -- Path to WAV (NULL if rotated out)
    is_quarterly_archive INTEGER DEFAULT 0, -- 1 if this is a preserved snapshot
    
    -- Exercise reference (v1.5)
    exercise_id TEXT,                     -- NULL for free recording
    exercise_score REAL                   -- Exercise-specific score if applicable
);

CREATE INDEX idx_sessions_timestamp ON sessions(timestamp);
CREATE INDEX idx_sessions_quarterly ON sessions(is_quarterly_archive);


-- ═══════════════════════════════════════════════════════════════════
-- CONFIG TABLE
-- User preferences and targets
-- ═══════════════════════════════════════════════════════════════════

CREATE TABLE config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL              -- ISO 8601
);

-- Default config entries (inserted on first run):
--
-- target_pitch_min_hz       | 155
-- target_pitch_max_hz       | 220
-- target_resonance_min      | 50
-- target_resonance_max      | 100
-- keybind                   | right_option
-- overlay_position          | top_center
-- summary_display_seconds   | 10
-- rolling_clip_count        | 30
-- quarterly_archive_days    | 90


-- ═══════════════════════════════════════════════════════════════════
-- EXERCISES TABLE (v1.5)
-- Guided exercise definitions
-- ═══════════════════════════════════════════════════════════════════

CREATE TABLE exercises (
    id TEXT PRIMARY KEY,                  -- e.g., "pitch_hold_180"
    name TEXT NOT NULL,                   -- "Hold 180 Hz"
    category TEXT NOT NULL,               -- "pitch", "resonance", "combined"
    description TEXT,                     -- Instructions for the user
    target_pitch_hz REAL,                 -- Target pitch (if applicable)
    target_resonance REAL,                -- Target resonance (if applicable)
    duration_seconds REAL,                -- How long to hold/practice
    difficulty INTEGER DEFAULT 1          -- 1-5 scale
);


-- ═══════════════════════════════════════════════════════════════════
-- EXERCISE HISTORY TABLE (v1.5)
-- Track progress on specific exercises
-- ═══════════════════════════════════════════════════════════════════

CREATE TABLE exercise_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exercise_id TEXT NOT NULL,
    session_id INTEGER NOT NULL,
    completed_at TEXT NOT NULL,           -- ISO 8601
    score REAL,                           -- How close to target (0-100)
    notes TEXT,                           -- Optional user notes
    
    FOREIGN KEY (exercise_id) REFERENCES exercises(id),
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

CREATE INDEX idx_exercise_history_exercise ON exercise_history(exercise_id);
```

### File Structure

```
~/.fern/
├── fern.db                              # SQLite database
├── config.toml                          # Human-editable config
│
├── clips/
│   ├── rolling/                         # Most recent 30 clips
│   │   ├── 0001.wav
│   │   ├── 0002.wav
│   │   └── ... (FIFO, oldest deleted when > 30)
│   │
│   └── archive/                         # Quarterly snapshots (kept forever)
│       ├── 2026-Q1.wav
│       ├── 2026-Q2.wav
│       └── ...
│
├── charts/
│   └── latest_summary.png               # Most recent summary chart
│
└── logs/
    └── fern.log                         # Debug logs (optional)
```

### Configuration File

```toml
# ~/.fern/config.toml
# Human-editable configuration for Fern

[targets]
# Your personal target ranges
# Feminine range is roughly 155-255 Hz for pitch
# Adjust based on your goals and comfort
pitch_min_hz = 155
pitch_max_hz = 220
resonance_min = 50      # Brightness score 0-100
resonance_max = 100

[interface]
# Where to show the overlay
# Options: top_center, top_left, top_right, bottom_center
overlay_position = "top_center"

# How long to show the summary chart (seconds)
summary_display_seconds = 10

# Keybind (must match what you configure in Hammerspoon)
keybind = "right_option"

[storage]
# How many recent clips to keep
rolling_clip_count = 30

# How often to archive a clip (days)
quarterly_archive_days = 90

[analysis]
# Minimum recording duration to analyze (seconds)
min_duration_seconds = 0.5

# Analysis chunk size for live feedback (seconds)
chunk_duration_seconds = 0.1
```

### Audio Retention Logic

```
┌─────────────────────────────────────────────────────────────────────┐
│                     AUDIO RETENTION FLOW                            │
│                                                                     │
│  New Recording                                                      │
│       │                                                             │
│       ▼                                                             │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Save to rolling buffer as NNNN.wav                         │   │
│  │  (increment counter, wrap at 9999)                          │   │
│  └─────────────────────────────────────────────────────────────┘   │
│       │                                                             │
│       ▼                                                             │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Count files in rolling/                                    │   │
│  │  If count > 30:                                             │   │
│  │    - Find oldest file (by filename number)                  │   │
│  │    - Delete it                                              │   │
│  │    - Update any session records (set audio_clip_path=NULL)  │   │
│  └─────────────────────────────────────────────────────────────┘   │
│       │                                                             │
│       ▼                                                             │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Check quarterly archive:                                   │   │
│  │    - Query: SELECT MAX(timestamp) FROM sessions             │   │
│  │             WHERE is_quarterly_archive = 1                  │   │
│  │    - If NULL or > 90 days ago:                              │   │
│  │        • Mark current session: is_quarterly_archive = 1     │   │
│  │        • Copy clip to archive/YYYY-QN.wav                   │   │
│  │        • This clip is now protected from rolling deletion   │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘


TIMELINE EXAMPLE
════════════════

  Jan 1      Jan 15     Feb 1      Apr 1      Apr 5
    │          │          │          │          │
    ▼          ▼          ▼          ▼          ▼
  ┌────┐    ┌────┐     ┌────┐    ┌────┐    ┌────┐
  │ Q1 │    │ 05 │     │ 30 │    │ Q2 │    │ 02 │
  │arch│    │roll│     │roll│    │arch│    │roll│
  └────┘    └────┘     └────┘    └────┘    └────┘
    ▲                              ▲
    │                              │
  First recording              91 days later,
  of year archived             new archive created
```

---

## User Interface

### Live Overlay (During Recording)

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│   POSITION: Top center of screen, just below Hex's pill             │
│   SIZE: ~120 x 60 pixels                                            │
│   BACKGROUND: Semi-transparent dark (#1a1a1a at 85% opacity)        │
│   BORDER: Subtle rounded corners (8px radius)                       │
│                                                                     │
│   ┌──────────────────────────────────────────────────────────┐      │
│   │                                                          │      │
│   │         ●                    ●                           │      │
│   │       pitch              resonance                       │      │
│   │                                                          │      │
│   │   ───────────────────────────────────────────────────    │      │
│   │      target zone (subtle horizontal band)                │      │
│   │                                                          │      │
│   └──────────────────────────────────────────────────────────┘      │
│                                                                     │
│   BEHAVIOR:                                                         │
│   • Dots move VERTICALLY based on current value                     │
│   • Higher pitch/resonance = higher position                        │
│   • Dot COLOR indicates relationship to target:                     │
│       - In target range: Soft green (#7cb87c)                       │
│       - Below target: Gradient toward amber (#d4a574)               │
│       - Above target: Gradient toward blue (#74a4d4)                │
│   • A subtle horizontal band shows the target zone                  │
│   • Updates at ~15 fps (smooth but not CPU-hungry)                  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘


DOT POSITION MAPPING
════════════════════

    Overlay height: 60px
    Usable range: 10px to 50px (40px range)

    Pitch mapping:
        80 Hz  → y = 50 (bottom)
        280 Hz → y = 10 (top)
        Linear interpolation between

    Resonance mapping:
        0 (dark)   → y = 50 (bottom)
        100 (bright) → y = 10 (top)


DOT COLOR MAPPING
═════════════════

    Target range defined in config (e.g., 155-220 Hz)

    If value < target_min:
        Color lerps from green → amber based on distance
        At 30 Hz below: full amber

    If value > target_max:
        Color lerps from green → blue based on distance
        At 30 Hz above: full blue

    If value in target range:
        Soft green
```

### Summary View (After Recording)

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│   POSITION: Same location, expands from live overlay                │
│   SIZE: ~300 x 200 pixels                                           │
│   APPEARS: When hotkey is released                                  │
│   DURATION: 10 seconds, then fades out (configurable)               │
│                                                                     │
│   ╭──────────────────────────────────────────────────────────────╮  │
│   │                                                              │  │
│   │   ┌──────────────────────────────────────────────────────┐   │  │
│   │   │                                                      │   │  │
│   │   │         ╱╲      pitch over time                      │   │  │
│   │   │   ─────╱──╲─────────────────────── target zone       │   │  │
│   │   │       ╱    ╲    ╱╲                 (shaded)          │   │  │
│   │   │      ╱      ╲  ╱  ╲                                  │   │  │
│   │   │     ╱        ╲╱    ╲                                 │   │  │
│   │   │    ╱                ╲───────                         │   │  │
│   │   │                                                      │   │  │
│   │   └──────────────────────────────────────────────────────┘   │  │
│   │                                                              │  │
│   │   Avg: 178 Hz   │   Res: 67%   │   Duration: 12.3s           │  │
│   │                                                              │  │
│   │   ─────────────────────────────────────────────────────────  │  │
│   │   [P] replay                              [Esc] dismiss      │  │
│   │                                                              │  │
│   ╰──────────────────────────────────────────────────────────────╯  │
│                                                                     │
│   BEHAVIOR:                                                         │
│   • Chart shows pitch as primary line (time on x-axis)              │
│   • Target range shown as shaded horizontal band                    │
│   • Resonance could be a secondary, more subtle line                │
│   • Stats shown below chart in compact format                       │
│   • Hotkey hints at bottom                                          │
│   • Pressing P plays back the recording                             │
│   • Pressing Esc dismisses immediately                              │
│   • Fades out after 10 seconds if no interaction                    │
│   • Next recording automatically dismisses this view                │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Exercise Mode UI (v1.5)

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│   EXERCISE OVERLAY (replaces standard overlay during exercise)      │
│                                                                     │
│   ╭──────────────────────────────────────────────────────────────╮  │
│   │                                                              │  │
│   │   Exercise: Hold 180 Hz                                      │  │
│   │                                                              │  │
│   │   ┌──────────────────────────────────────────────────────┐   │  │
│   │   │                         ●  ← your pitch              │   │  │
│   │   │   ════════════════════════════════════  ← target     │   │  │
│   │   │                                                      │   │  │
│   │   └──────────────────────────────────────────────────────┘   │  │
│   │                                                              │  │
│   │           ████████████████░░░░░░░░  15s / 30s                │  │
│   │                                                              │  │
│   │   Accuracy: 73%                                              │  │
│   │                                                              │  │
│   ╰──────────────────────────────────────────────────────────────╯  │
│                                                                     │
│   ELEMENTS:                                                         │
│   • Exercise name at top                                            │
│   • Target line (fixed horizontal line at target pitch)             │
│   • Your pitch dot (moves vertically, trying to match target)       │
│   • Progress bar showing time remaining                             │
│   • Live accuracy percentage                                        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Command-Line Interface

### Command Structure

```
fern
├── log
│   ├── recent [N]              Show N most recent sessions (default: 10)
│   ├── stats                   Overall statistics
│   │   ├── --week              This week only
│   │   ├── --month             This month only
│   │   └── --all               All time (default)
│   ├── progress                Compare quarterly archives
│   │   └── --chart             Open visual chart
│   ├── search                  Query sessions
│   │   ├── --pitch ">180"      Filter by pitch
│   │   ├── --resonance ">60"   Filter by resonance
│   │   ├── --date "2026-01"    Filter by date
│   │   └── --exercise "..."    Filter by exercise (v1.5)
│   └── export
│       ├── csv                 Export to CSV
│       └── json                Export to JSON
│
├── audio
│   ├── list                    Show rolling 30 clips
│   ├── play [N|latest]         Play clip N or most recent
│   ├── archive                 List quarterly archives
│   └── play-archive [Q]        Play archived clip (e.g., 2026-Q1)
│
├── config
│   ├── (no args)               Show current config
│   ├── set KEY VALUE           Update a config value
│   ├── edit                    Open config.toml in $EDITOR
│   └── reset                   Reset to defaults
│
├── exercise (v1.5)
│   ├── list                    Show available exercises
│   │   ├── --category pitch    Filter by category
│   │   └── --difficulty 1-3    Filter by difficulty
│   ├── start [ID]              Start an exercise
│   ├── history                 Show exercise completion history
│   │   └── --exercise [ID]     Filter to specific exercise
│   └── progress                Show improvement over exercises
│
└── daemon                      Run in daemon mode (used by Hammerspoon)
    ├── --start                 Begin recording
    └── --stop                  Stop and analyze
```

### Example CLI Output

```
$ fern log recent

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                        Recent Sessions                              ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

  #   Time              Duration   Pitch (avg)   Resonance   In Target
 ─────────────────────────────────────────────────────────────────────
  1   Today 2:34 PM     12.3s      178 Hz        67%         84%
  2   Today 2:31 PM     8.7s       165 Hz        62%         71%
  3   Today 2:28 PM     15.1s      182 Hz        70%         89%
  4   Today 11:15 AM    6.2s       159 Hz        58%         65%
  5   Yesterday 4:45 PM 22.8s      174 Hz        65%         79%

  Showing 5 of 847 sessions. Use 'fern log recent 20' for more.


$ fern log stats --week

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                      This Week's Stats                              ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

  Sessions:          47
  Total Duration:    8m 32s
  
  Pitch:
    Average:         172 Hz
    Range:           145 - 203 Hz
    Std Dev:         18 Hz
    In Target:       76%
  
  Resonance:
    Average:         64%
    In Target:       71%
  
  Trend:             ↑ Pitch up 4 Hz from last week
                     ↑ Resonance up 3% from last week


$ fern log progress

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                     Quarterly Progress                              ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

  Quarter     Pitch (avg)    Resonance    Sessions    Archived
 ─────────────────────────────────────────────────────────────────────
  2026 Q1     172 Hz         64%          283         ✓ Play: fern audio play-archive 2026-Q1
  2025 Q4     158 Hz         52%          412         ✓ Play: fern audio play-archive 2025-Q4
  2025 Q3     149 Hz         47%          89          ✓ Play: fern audio play-archive 2025-Q3

  Change Q4→Q1:  ↑ +14 Hz pitch  ↑ +12% resonance

  🌱 You're making real progress. Keep going.


$ fern audio list

  Rolling Clips (30 most recent):
 ─────────────────────────────────────────────────────────────────────
   1. 0847.wav   Today 2:34 PM      12.3s   178 Hz
   2. 0846.wav   Today 2:31 PM      8.7s    165 Hz
   3. 0845.wav   Today 2:28 PM      15.1s   182 Hz
   ...
  30. 0818.wav   Jan 28 9:12 AM     4.2s    161 Hz

  Play with: fern audio play 1


$ fern exercise list

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                     Available Exercises                             ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

  PITCH EXERCISES
  ───────────────
  pitch_hold_160      Hold 160 Hz           ★☆☆   30s
  pitch_hold_180      Hold 180 Hz           ★★☆   30s
  pitch_hold_200      Hold 200 Hz           ★★★   30s
  pitch_glide_up      Glide 150→200 Hz      ★★☆   15s
  pitch_glide_down    Glide 200→150 Hz      ★★☆   15s

  RESONANCE EXERCISES
  ───────────────────
  resonance_bright    Maximize brightness   ★★☆   20s
  resonance_forward   Forward placement     ★★☆   20s

  COMBINED EXERCISES
  ──────────────────
  combined_180_70     180 Hz + 70% res      ★★★   30s
  sentence_feminine   Read sentence         ★★☆   varies

  Start with: fern exercise start pitch_hold_160
```

---

## Guided Exercises (v1.5)

### Philosophy

Exercises are structured practice for when you want focused training, not just passive feedback. They provide:

1. **Clear targets** — hit this pitch, hold this resonance
2. **Immediate feedback** — see how close you are in real-time
3. **Progress tracking** — watch yourself improve over time
4. **Graduated difficulty** — start easy, increase challenge

### Exercise Categories

```
┌─────────────────────────────────────────────────────────────────────┐
│                     EXERCISE TAXONOMY                                │
│                                                                     │
│  PITCH EXERCISES                                                    │
│  ───────────────                                                    │
│  • Pitch Hold: Sustain a specific frequency                         │
│      - pitch_hold_160 (160 Hz, 30s, ★☆☆)                           │
│      - pitch_hold_180 (180 Hz, 30s, ★★☆)                           │
│      - pitch_hold_200 (200 Hz, 30s, ★★★)                           │
│                                                                     │
│  • Pitch Glide: Smoothly transition between frequencies             │
│      - pitch_glide_up (150→200 Hz, 15s, ★★☆)                       │
│      - pitch_glide_down (200→150 Hz, 15s, ★★☆)                     │
│      - pitch_siren (150→200→150 Hz, 20s, ★★★)                      │
│                                                                     │
│  • Pitch Variation: Practice expressiveness                         │
│      - pitch_question (rise at end, 10s, ★★☆)                      │
│      - pitch_statement (fall at end, 10s, ★★☆)                     │
│                                                                     │
│  RESONANCE EXERCISES                                                │
│  ───────────────────                                                │
│  • Resonance Brightness: Maximize forward placement                 │
│      - resonance_bright (target: 70%+, 20s, ★★☆)                   │
│      - resonance_forward (focus on mask, 20s, ★★☆)                 │
│                                                                     │
│  • Resonance Contrast: Feel the difference                          │
│      - resonance_contrast (chest→head, 30s, ★★★)                   │
│                                                                     │
│  COMBINED EXERCISES                                                 │
│  ──────────────────                                                 │
│  • Full Voice: Hit both targets simultaneously                      │
│      - combined_170_60 (170 Hz + 60% res, 30s, ★★☆)                │
│      - combined_180_70 (180 Hz + 70% res, 30s, ★★★)                │
│      - combined_190_75 (190 Hz + 75% res, 30s, ★★★)                │
│                                                                     │
│  • Sentence Reading: Apply to real speech                           │
│      - sentence_rainbow (Rainbow Passage, varies, ★★☆)             │
│      - sentence_custom (user-provided text, varies, ★★☆)           │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Exercise Flow

```
START EXERCISE
══════════════

  $ fern exercise start pitch_hold_180
       │
       ▼
  ┌─────────────────────────────────────────────────────────────┐
  │  Load exercise definition from database                     │
  │  Display instructions in terminal:                          │
  │                                                             │
  │    "Exercise: Hold 180 Hz                                   │
  │     Try to sustain a pitch of 180 Hz for 30 seconds.        │
  │     Focus on keeping the tone steady.                       │
  │                                                             │
  │     Press ENTER when ready, or Q to quit."                  │
  │                                                             │
  └─────────────────────────────────────────────────────────────┘
       │
       │ user presses ENTER
       ▼
  ┌─────────────────────────────────────────────────────────────┐
  │  Signal Hammerspoon to show EXERCISE OVERLAY                │
  │  (different from standard overlay)                          │
  │                                                             │
  │  Begin countdown: 3... 2... 1... GO                         │
  │                                                             │
  │  Start recording + analysis                                 │
  └─────────────────────────────────────────────────────────────┘
       │
       │ duration complete or user stops
       ▼
  ┌─────────────────────────────────────────────────────────────┐
  │  Calculate score:                                           │
  │    - % of time within ±10 Hz of target                      │
  │    - Average deviation from target                          │
  │    - Stability (lower std dev = better)                     │
  │                                                             │
  │  Save to exercise_history                                   │
  │  Save session with exercise_id reference                    │
  │                                                             │
  │  Display results:                                           │
  │    "Score: 73%                                              │
  │     Average: 176 Hz (target: 180)                           │
  │     Stability: Good                                         │
  │                                                             │
  │     Your best for this exercise: 81% (Jan 28)"              │
  │                                                             │
  └─────────────────────────────────────────────────────────────┘
```

### Scoring System

```
PITCH HOLD SCORING
══════════════════

  Target: 180 Hz
  Tolerance: ±10 Hz (configurable)
  
  For each analysis frame:
    if |pitch - target| <= 10:
      in_target_frames += 1
    
  score = (in_target_frames / total_frames) * 100

  Bonus modifiers:
    - Stability bonus: if std_dev < 5 Hz, score += 5
    - Consistency bonus: if no large jumps (>20 Hz), score += 5

  Final score capped at 100


PITCH GLIDE SCORING
═══════════════════

  Target: Linear interpolation from start_pitch to end_pitch
  
  At time t (0 to duration):
    expected_pitch = start_pitch + (end_pitch - start_pitch) * (t / duration)
    
  Score based on average deviation from expected trajectory


COMBINED SCORING
════════════════

  pitch_score = (as above)
  resonance_score = (similar calculation for resonance)
  
  combined_score = (pitch_score * 0.6) + (resonance_score * 0.4)
  
  (Pitch weighted higher because it's more controllable initially)
```

---

## Implementation Phases

### Phase 1: Foundation (Day 1)

**Goal:** Prove the core analysis works

```
Tasks:
├── [ ] Create project structure
│       fern/
│       ├── __init__.py
│       ├── capture.py
│       ├── analysis.py
│       ├── db.py
│       ├── audio_manager.py
│       ├── charts.py
│       ├── cli.py
│       └── daemon.py
│
├── [ ] Set up pyproject.toml with dependencies
├── [ ] Write capture.py: record audio to WAV file
├── [ ] Write analysis.py: extract pitch from WAV using librosa
├── [ ] Test with a recorded sample of your voice
└── [ ] Verify pitch values are in reasonable range (80-300 Hz for speech)

Deliverable: Python script that records audio and prints pitch statistics
```

### Phase 2: Resonance Analysis (Day 1-2)

**Goal:** Add formant/resonance extraction

```
Tasks:
├── [ ] Install praat-parselmouth
├── [ ] Add R1 (first formant) extraction to analysis.py
├── [ ] Create brightness score from R1 relative to pitch
│       brightness = normalize(R1 - pitch) to 0-100 scale
├── [ ] Test with voice samples
└── [ ] Calibrate target ranges based on your voice

Deliverable: Script prints pitch AND resonance metrics
```

### Phase 3: Database + CLI Skeleton (Day 2)

**Goal:** Persistent storage and basic queries

```
Tasks:
├── [ ] Create ~/.fern/ directory structure
├── [ ] Write db.py: SQLite schema creation, insert, query
├── [ ] Write config.toml handling
├── [ ] Scaffold Typer CLI structure
├── [ ] Implement: fern log recent
├── [ ] Implement: fern log stats
├── [ ] Implement: fern config (view/set)
└── [ ] Test: record → save → query cycle

Deliverable: Can save analysis to DB and query via CLI
```

### Phase 4: Audio Management (Day 2-3)

**Goal:** Rolling clips + quarterly archives

```
Tasks:
├── [ ] Write audio_manager.py
├── [ ] Implement rolling buffer (keep 30, FIFO deletion)
├── [ ] Implement quarterly archive detection and copying
├── [ ] Implement: fern audio list
├── [ ] Implement: fern audio play
├── [ ] Implement: fern audio archive
├── [ ] Implement: fern audio play-archive
└── [ ] Test with smaller buffer (keep 5) to verify rotation

Deliverable: Full audio lifecycle working
```

### Phase 5: Live Capture Mode (Day 3)

**Goal:** Real-time streaming analysis

```
Tasks:
├── [ ] Modify capture.py for streaming mode
│       - Use sounddevice callback for continuous capture
│       - Buffer audio in chunks (100ms)
├── [ ] Analyze chunks in real-time
├── [ ] Output JSON lines to stdout:
│       {"type": "live", "pitch_hz": 178.3, "resonance": 67.2}
├── [ ] Handle start signal (begin capture)
├── [ ] Handle stop signal (final analysis + summary)
├── [ ] Output final JSON:
│       {"type": "summary", "pitch_mean": 175.2, ..., "chart_path": "..."}
└── [ ] Test daemon mode manually

Deliverable: `python -m fern daemon --start` streams live JSON
```

### Phase 6: Chart Generation (Day 3)

**Goal:** Visual summary charts

```
Tasks:
├── [ ] Write charts.py
├── [ ] Generate pitch-over-time line chart
├── [ ] Add shaded region for target range
├── [ ] Add resonance as secondary line (more subtle)
├── [ ] Add summary stats below chart
├── [ ] Save as PNG to ~/.fern/charts/latest_summary.png
└── [ ] Style: dark theme, minimal, readable at small size

Deliverable: Summary chart PNG generated after each recording
```

### Phase 7: Hammerspoon Integration (Day 3-4)

**Goal:** GUI layer that ties everything together

```
Tasks:
├── [ ] Install Hammerspoon
├── [ ] Create ~/.hammerspoon/init.lua
├── [ ] Create fern.lua module
├── [ ] Implement hotkey listener (right_option)
├── [ ] On key down:
│       ├── Show "listening" indicator
│       ├── Spawn Python daemon process
│       └── Begin reading JSON from stdout
├── [ ] Create canvas for live overlay (2 dots)
├── [ ] Parse live JSON, update dot positions/colors
├── [ ] On key up:
│       ├── Send stop signal to daemon
│       ├── Read summary JSON
│       ├── Display chart image
│       └── Show hotkey hints
├── [ ] Handle P key: play audio clip
├── [ ] Handle Esc: dismiss overlay
├── [ ] Auto-fade after 10 seconds
└── [ ] Test full flow: hold key → see dots → release → see chart

Deliverable: Working end-to-end voice feedback!
```

### Phase 8: Polish (Day 4-5)

**Goal:** Make it robust for daily use

```
Tasks:
├── [ ] Error handling: no mic, permission denied, etc.
├── [ ] Implement: fern log progress (quarterly comparison)
├── [ ] Implement: fern log search
├── [ ] Implement: fern log export
├── [ ] Add fern.log for debugging
├── [ ] Test with various recording lengths
├── [ ] Handle edge cases: very short recordings, silence, noise
└── [ ] Documentation: README, setup instructions

Deliverable: Production-ready for daily use
```

### Phase 9: Guided Exercises (v1.5, Day 5+)

**Goal:** Structured practice mode

```
Tasks:
├── [ ] Add exercises and exercise_history tables
├── [ ] Seed default exercises (pitch holds, glides, combined)
├── [ ] Implement: fern exercise list
├── [ ] Implement: fern exercise start [ID]
│       ├── Show instructions in terminal
│       ├── Signal Hammerspoon for exercise overlay
│       ├── Run exercise with timer
│       └── Calculate and display score
├── [ ] Create exercise overlay variant in Hammerspoon
│       ├── Target line (fixed)
│       ├── Current value dot (moving)
│       ├── Progress bar
│       └── Live accuracy percentage
├── [ ] Implement: fern exercise history
├── [ ] Implement: fern exercise progress
├── [ ] Add best-score tracking per exercise
└── [ ] Consider: custom exercises, user-defined targets

Deliverable: Full guided exercise system
```

---

## Security Considerations

### Permissions Required

- **Microphone access** — required for audio capture
- **Accessibility** — required for global hotkey (via Hammerspoon)

### Data Privacy

- All data stored locally in `~/.fern/`
- No network requests, no telemetry, no cloud sync
- Audio clips are personal voice recordings — handle with care
- Consider: encrypted storage option for sensitive users

### File Permissions

```bash
~/.fern/              drwx------  (700)
~/.fern/fern.db       -rw-------  (600)
~/.fern/clips/        drwx------  (700)
~/.fern/config.toml   -rw-------  (600)
```

---

## Dependencies

### Python (pyproject.toml)

```toml
[project]
name = "fern"
version = "0.1.0"
description = "Voice training feedback companion"
requires-python = ">=3.11"
dependencies = [
    "sounddevice>=0.4.6",        # Audio capture
    "numpy>=1.24.0",             # Array operations
    "librosa>=0.10.0",           # Pitch detection
    "praat-parselmouth>=0.4.3",  # Formant analysis
    "matplotlib>=3.7.0",         # Chart generation
    "typer[all]>=0.9.0",         # CLI framework
    "rich>=13.0.0",              # Pretty terminal output
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
]

[project.scripts]
fern = "fern.cli:app"
```

### System (Homebrew)

```bash
brew install portaudio          # Required for sounddevice
brew install --cask hammerspoon # GUI layer
```

---

## Future Ideas (Post v1.5)

```
┌─────────────────────────────────────────────────────────────────────┐
│                        FUTURE POSSIBILITIES                          │
│                                                                     │
│  ANALYSIS                                                           │
│  • Spectrogram view for the curious                                 │
│  • Breathiness detection                                            │
│  • Speech rate / pacing analysis                                    │
│  • Filler word detection ("um", "uh")                               │
│                                                                     │
│  EXERCISES                                                          │
│  • Custom user-defined exercises                                    │
│  • Exercise sequences / routines                                    │
│  • Adaptive difficulty (auto-adjust based on progress)              │
│  • Sentence bank with phonetically balanced passages                │
│                                                                     │
│  GAMIFICATION                                                       │
│  • Daily streaks                                                    │
│  • Achievement badges                                               │
│  • Progress milestones                                              │
│                                                                     │
│  SOCIAL (careful, optional, privacy-first)                          │
│  • Share progress charts (export image)                             │
│  • Compare with voice coach (send recording)                        │
│                                                                     │
│  INTEGRATION                                                        │
│  • Sync with Voice Tools app                                        │
│  • Export to speech therapist format                                │
│  • Shortcuts.app integration                                        │
│                                                                     │
│  PLATFORM                                                           │
│  • iOS companion app (view stats, play archives)                    │
│  • Linux support (different GUI layer)                              │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Closing

Fern isn't about perfection. It's about presence. About showing up, word by word, and paying just a little more attention to the voice that's becoming yours.

The forest doesn't judge how fast you grow. Neither does Fern. It just watches, reflects, and reminds you: every word is practice.

```
              🌿

         every word
         is practice

         every day
         a little closer

         to her
```
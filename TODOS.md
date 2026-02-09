# Fern - Task List

## Phase 1: Foundation

Goal: Basic pitch detection from microphone

- [x] Set up UV project with pyproject.toml
- [x] Install core dependencies (sounddevice, librosa, praat-parselmouth, numpy)
- [x] Create basic pitch detection script (`scripts/test_pitch.py`)
  - Capture 5 seconds of audio from microphone
  - Extract fundamental frequency using praat-parselmouth
  - Print median pitch to console
- [x] Verify audio capture works on macOS
- [x] Add CLI entry point (`fern` command using Typer)
- [x] Create tests/ directory with initial test structure

## Phase 2: Data Layer

- [x] Implement SQLite schema in `db.py`
  - sessions table
  - readings table
  - targets table
  - config table
- [x] Create data models in `models.py`
- [x] Implement audio clip storage in `~/.fern/clips/`
- [x] Add rolling archive logic (keep 30 most recent clips)

## Phase 3: Core Analysis

- [x] Implement `capture.py` with callback-based audio capture
- [x] Implement `analysis.py` with pitch extraction
- [x] Implement resonance analysis using librosa
- [x] Create Session/Reading lifecycle management
- [ ] Add basic CLI commands: `fern status`, `fern trend`

## Phase 4: Hammerspoon Integration

- [x] Create `websocket_server.py` for IPC
- [x] Implement `hammerspoon/init.lua` with hotkey detection
- [x] Add signal file communication (`/tmp/fern_capture_active`)
- [x] Create `hammerspoon/overlay.lua` for live display
- [x] Create `hammerspoon/charts.lua` for trend visualization

## Phase 5: CLI Polish

- [x] Add Rich terminal formatting
- [x] Implement `fern config set-target` command
- [x] Add `fern review <session-id>` command
- [x] Add `fern sessions` command
- [x] Create sparkline visualizations for trends
- [x] Add export functionality (CSV, JSON)
- [x] Add `fern config:show` command

## Phase 6: Charts

- [x] Implement `hammerspoon/charts.lua`
- [x] Add historical trend visualization
- [x] Create target range indicators on charts
- [x] Add keyboard navigation for chart view
- [x] Implement `hammerspoon/chart_view.lua` with full navigation
- [x] Add view toggle (trend, resonance, summary)
- [x] Add time range selection (7d, 30d, 90d)
- [x] Add help overlay with keyboard shortcuts
- [x] Add `fern chart` CLI command

## Phase 7: Installation & Packaging

- [ ] Create install script
- [ ] Add Hammerspoon config setup instructions
- [ ] Create Homebrew formula (optional)
- [ ] Write comprehensive README documentation
- [ ] Add LICENSE file

## Phase 8: v1.0 Polish

- [ ] Add comprehensive error handling
- [ ] Implement logging system
- [ ] Create test suite with pytest
- [ ] Add type hints throughout
- [ ] Performance optimization

## Phase 9: Guided Exercises (v1.5)

- [ ] Design exercise data model
- [ ] Create pitch glide exercise
- [ ] Add resonance shifting exercise
- [ ] Implement exercise progress tracking
- [ ] Add exercise recommendations based on trends

---

## Notes

- See [Fern-Spec.md](Fern-Spec.md) for complete technical specification
- Repository: https://github.com/autumnsgrove/fern

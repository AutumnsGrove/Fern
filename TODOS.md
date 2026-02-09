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

- [ ] Create `websocket_server.py` for IPC
- [ ] Implement `hammerspoon/init.lua` with hotkey detection
- [ ] Add signal file communication (`/tmp/fern_capture_active`)
- [ ] Create `hammerspoon/overlay.lua` for live display
- [ ] Test Python/Hammerspoon communication

## Phase 5: CLI Polish

- [ ] Add Rich terminal formatting
- [ ] Implement `fern config set-target` command
- [ ] Add `fern review <session-id>` command
- [ ] Create sparkline visualizations for trends
- [ ] Add export functionality (CSV, JSON)

## Phase 6: Charts

- [ ] Implement `hammerspoon/charts.lua`
- [ ] Add historical trend visualization
- [ ] Create target range indicators on charts
- [ ] Add keyboard navigation for chart view

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

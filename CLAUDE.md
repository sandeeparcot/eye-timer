# CLAUDE.md — Eye Timer

Developer reference for AI assistants working on this codebase.

---

## Project overview

Eye Timer is a macOS menu bar app implementing the NHS 20-20-20 rule for digital eye strain prevention: every 20 minutes, look 20 feet away for 20 seconds. Its distinguishing feature is that it **pauses on screen lock and resets on unlock** — something no other app does correctly.

- Language: Python 3.9+
- Platform: macOS 12.0 (Monterey) or later, menu bar only (no Dock icon)
- Version: 1.0.0
- License: Apache 2.0; "Eye Timer" trademark owned by Sandeep Arcot

---

## Repository layout

```
eye_timer.py      # entire application (~200 lines)
setup_app.py      # py2app packaging config
build.sh          # build → sign → DMG → notarise pipeline
entitlements.plist # macOS code-signing entitlements
README.md
LICENSE           # Apache 2.0
NOTICE            # trademark & attribution notices
```

There are no tests, no linter configs, no requirements.txt, and no `__init__.py`. The whole app lives in one file.

---

## Architecture

### `eye_timer.py`

**Two classes, one module:**

#### `ScreenObserver(NSObject)` — lines 24–34
PyObjC Objective-C subclass. Registered with `NSDistributedNotificationCenter` to receive two system-wide events:
- `com.apple.screenIsLocked` → calls `EyeTimerApp.on_screen_lock()`
- `com.apple.screenIsUnlocked` → calls `EyeTimerApp.on_screen_unlock()`

The observer must be kept alive for the lifetime of the app (held as `self._observer` on the app instance).

#### `EyeTimerApp(rumps.App)` — lines 37–200
Main application. Key state:

| Attribute | Type | Meaning |
|---|---|---|
| `remaining` | int | Seconds left in current phase |
| `mode` | str | `"work"` or `"rest"` |
| `running` | bool | Whether the 1-second ticker is active |
| `breaks` | int | Total breaks taken this session |

**Timer cycle:**
1. `WORK_SEC = 1200` (20 min) counts down → fires work→rest notification
2. `REST_SEC = 20` (20 sec) counts down → fires rest→work notification
3. Repeats indefinitely

**`_tick()`** is called every second by `rumps.Timer`. When `remaining` hits 0 it transitions the mode and fires a native notification. No threading — rumps runs on the main run loop.

**Display:**
- Work phase: menu bar title `👁 MM:SS`, menu item `Work — MM:SS until break`
- Rest phase: menu bar title `🌿 SSs`, menu item `Rest — look away for Ss`

**Screen lock/unlock flow:**
- `on_screen_lock()`: pauses ticker, sets static status text
- `on_screen_unlock()`: calls `_reset_state()` + `_start()` + fires a welcome-back notification

**Dock hiding:** `NSApplicationActivationPolicyProhibited` is set after `super().__init__()` — order matters because NSApp isn't fully initialised until the rumps constructor runs.

**`argv_emulation: False`** in `setup_app.py` is required for menu bar apps; `True` hangs the process.

---

## Dependencies

Install at runtime (no requirements.txt):
```bash
pip3 install rumps pyobjc-framework-Cocoa
```

Build-only:
```bash
pip3 install py2app
```

System tool for DMG creation (optional):
```bash
brew install create-dmg
```

---

## Running from source

```bash
pip3 install rumps pyobjc-framework-Cocoa
python3 eye_timer.py
```

The `👁 20:00` icon appears in the menu bar immediately. There is no CLI output — logs go nowhere.

---

## Building a distributable `.app`

```bash
pip3 install py2app rumps pyobjc-framework-Cocoa
python3 setup_app.py py2app
```

Output: `dist/Eye Timer.app`

The full pipeline (sign + DMG + notarise) is in `build.sh`. Fill in `DEVELOPER_ID`, `APPLE_ID`, and `TEAM_ID` before running. Without signing the app still works but macOS shows an "unidentified developer" warning.

### Bundle ID placeholder
`setup_app.py` has `"CFBundleIdentifier": "com.yourdomain.eyetimer"` — update this before publishing.

---

## Key conventions

- **Single-file app.** Do not split into multiple modules without a strong reason.
- **No comments unless the why is non-obvious.** The existing docstrings on `on_screen_lock` and `on_screen_unlock` are exceptions because the behaviour diverges from what the names suggest.
- **Constants at module level** (`TIPS`, `WORK_SEC`, `REST_SEC`) so they're easy to find and override.
- **`_reset_state()`** resets `breaks` to 0 — this is intentional; it's a session reset, not just a cycle reset. Keep this behaviour when touching the reset flow.
- **No `argv_emulation`** in py2app — do not change this.
- **PyObjC selector syntax**: method names follow Objective-C style with trailing underscores in Python (`addObserver_selector_name_object_`). Do not rename these.

---

## Notifications

Uses `rumps.notification(title, subtitle, message)`. macOS requires the user to grant notification permission on first run. The five rotating tips in `TIPS` cycle via `(self.breaks - 1) % len(TIPS)`.

---

## Missing files referenced in README

- `setup.sh` — auto-start on login script, not yet written
- `INSTRUCTIONS.md` — extended architecture notes, not yet written

Both are linked from README.md and need to be created if contributors ask about them.

---

## Roadmap (from README)

Completed:
- Menu bar countdown
- Auto-start on launch
- Screen lock / unlock detection
- Native notifications with rotating tips
- Daily break counter

Planned:
- Custom intervals (preferences panel)
- Do Not Disturb / Focus mode awareness
- Blink reminder (every 5 minutes)
- Weekly break report
- Calendar integration (auto-pause in meetings)
- Apple Health integration
- Optometrist-designed exercise library

---

## Git workflow

- Main branch: `main`
- Feature branches: `feature/<description>` (per README contributing guidelines)
- No CI, no pre-commit hooks, no linting pipeline as of v1.0.0

---

## What to watch out for

1. **macOS-only.** Nothing in this codebase will work on Linux or Windows. PyObjC and rumps are macOS-exclusive.
2. **No test suite.** Manual testing on a real Mac is the only verification path.
3. **Screen lock notifications are not guaranteed.** `NSDistributedNotificationCenter` events can be delayed or dropped under heavy system load. This is a macOS limitation.
4. **`_observer` must stay alive.** If the reference is lost, GC will collect the Objective-C object and lock/unlock events will silently stop arriving.
5. **`breaks` resets on any reset.** Both the user-triggered Reset menu item and the screen-unlock flow call `_reset_state()`, zeroing the daily counter. This is a known UX trade-off, not a bug.

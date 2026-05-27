#!/usr/bin/env python3
"""
20-20-20 Eye Timer — macOS Menu Bar App
· Auto-starts the timer on launch
· Pauses automatically when screen locks
· Resets to a fresh 20-min cycle on unlock

Requires: pip install rumps pyobjc-framework-Cocoa
"""

import rumps
from Foundation import NSDistributedNotificationCenter, NSObject
from AppKit import NSApplication, NSApplicationActivationPolicyProhibited

TIPS = [
    "Look at something at least 20 feet away.",
    "Blink slowly a few times to refresh your eyes.",
    "Let your eyes go soft — no need to focus on anything.",
    "Look out a window if you can — natural scenery is best.",
    "Roll your shoulders back and take a deep breath.",
]


class ScreenObserver(NSObject):
    """Listens for macOS screen lock/unlock distributed notifications."""

    def setApp_(self, app):
        self._app = app

    def handleLock_(self, _notification):
        self._app.on_screen_lock()

    def handleUnlock_(self, _notification):
        self._app.on_screen_unlock()


class EyeTimerApp(rumps.App):

    WORK_SEC = 20 * 60
    REST_SEC = 20

    def __init__(self):
        super().__init__("👁 20:00", quit_button=None)

        # Hide from Dock and Cmd+Tab — must be called after super().__init__()
        # so that NSApp is fully initialised before we set the policy
        NSApplication.sharedApplication().setActivationPolicy_(NSApplicationActivationPolicyProhibited)

        self.remaining = self.WORK_SEC
        self.mode      = "work"
        self.running   = False
        self.breaks    = 0

        self.status_item = rumps.MenuItem("Starting…")
        self.breaks_item = rumps.MenuItem("Breaks today: 0")
        self.toggle_btn  = rumps.MenuItem("⏸  Pause",   callback=self.toggle)
        self.reset_btn   = rumps.MenuItem("↺  Reset",   callback=self.reset)
        self.about_btn   = rumps.MenuItem("ℹ  About",   callback=self.about)
        self.quit_btn    = rumps.MenuItem("Quit",        callback=rumps.quit_application)

        self.menu = [
            self.status_item,
            self.breaks_item,
            None,
            self.toggle_btn,
            self.reset_btn,
            None,
            self.about_btn,
            None,
            self.quit_btn,
        ]

        self._ticker = rumps.Timer(self._tick, 1)
        self._register_screen_observer()
        self._start()   # auto-start immediately on launch

    # ── Screen lock / unlock ───────────────────────────────────────────────

    def _register_screen_observer(self):
        self._observer = ScreenObserver.new()
        self._observer.setApp_(self)
        nc = NSDistributedNotificationCenter.defaultCenter()
        nc.addObserver_selector_name_object_(
            self._observer, "handleLock:",   "com.apple.screenIsLocked",   None
        )
        nc.addObserver_selector_name_object_(
            self._observer, "handleUnlock:", "com.apple.screenIsUnlocked", None
        )

    def on_screen_lock(self):
        """Pause timer silently when screen locks."""
        if self.running:
            self._pause()
        self.status_item.title = "Screen locked — timer paused"
        self.title = "👁 ⏸"

    def on_screen_unlock(self):
        """Reset to fresh 20-min cycle and auto-resume on unlock."""
        self._reset_state()
        self._start()
        rumps.notification(
            title="👁  Welcome back!",
            subtitle="20-20-20 timer restarted",
            message="Timer reset — your eyes rested while locked.",
        )

    # ── Controls ───────────────────────────────────────────────────────────

    def about(self, _):
        rumps.alert(
            title="👁  Eye Timer  v1.0",
            message=(
                "Implements the NHS-recommended 20-20-20 rule.\n\n"
                "Every 20 minutes, look at something at least\n"
                "20 feet away for 20 seconds.\n\n"
                "• Auto-starts on login\n"
                "• Pauses when screen locks\n"
                "• Resets on unlock\n\n"
                "Free & open source\n"
                "© 2026 Sandeep Arcot\n"
                "eyetimer.app"
            ),
            ok="Close"
        )

    def toggle(self, _):
        if self.running:
            self._pause()
        else:
            self._start()

    def reset(self, _):
        self._reset_state()
        self._start()

    # ── Internal helpers ───────────────────────────────────────────────────

    def _start(self):
        self.running = True
        self.toggle_btn.title = "⏸  Pause"
        self._ticker.start()
        self._update_display()

    def _pause(self):
        self.running = False
        self.toggle_btn.title = "▶  Resume"
        self._ticker.stop()

    def _reset_state(self):
        self._ticker.stop()
        self.running = False
        self.mode = "work"
        self.remaining = self.WORK_SEC
        self.breaks = 0
        self.toggle_btn.title = "⏸  Pause"
        self.breaks_item.title = "Breaks today: 0"

    # ── Tick ───────────────────────────────────────────────────────────────

    def _tick(self, _):
        if self.remaining > 0:
            self.remaining -= 1
            self._update_display()
            return

        if self.mode == "work":
            self.mode = "rest"
            self.remaining = self.REST_SEC
            self.breaks += 1
            self.breaks_item.title = f"Breaks today: {self.breaks}"
            tip = TIPS[(self.breaks - 1) % len(TIPS)]
            rumps.notification(
                title="👁  Eye break time!",
                subtitle="Look 20 feet away for 20 seconds",
                message=tip,
            )
        else:
            self.mode = "work"
            self.remaining = self.WORK_SEC
            rumps.notification(
                title="✅  Break complete",
                subtitle="Back to work — next break in 20 min",
                message=f"Total breaks today: {self.breaks}",
            )
        self._update_display()

    # ── Display ────────────────────────────────────────────────────────────

    def _update_display(self):
        if self.mode == "work":
            m, s = divmod(self.remaining, 60)
            self.title = f"👁 {m:02d}:{s:02d}"
            self.status_item.title = f"Work — {m:02d}:{s:02d} until break"
        else:
            self.title = f"🌿 {self.remaining:02d}s"
            self.status_item.title = f"Rest — look away for {self.remaining}s"


if __name__ == "__main__":
    EyeTimerApp().run()

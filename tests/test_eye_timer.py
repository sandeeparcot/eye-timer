"""
Tests for eye_timer.py

All macOS-only dependencies (rumps, PyObjC) are stubbed out so the suite
runs on any platform, including Linux CI.

Run with:
    python -m pytest tests/
    python -m unittest discover tests/
"""

import sys
import types
import unittest
from unittest.mock import MagicMock


# ── Stubs for macOS-only modules (must be installed before importing eye_timer)


class _MockNSObject:
    """Minimal NSObject — provides the .new() Objective-C class constructor."""

    @classmethod
    def new(cls):
        return cls()


class _MockMenuItem:
    """Minimal rumps.MenuItem with a mutable title attribute."""

    def __init__(self, title, callback=None):
        self.title = title
        self.callback = callback

    def __repr__(self):
        return f"MenuItem({self.title!r})"


class _MockRumpsApp:
    """Minimal rumps.App base class."""

    def __init__(self, title, quit_button=None):
        self.title = title
        self.menu = []

    def run(self):  # pragma: no cover
        pass


def _make_rumps_module():
    m = types.ModuleType("rumps")
    m.App = _MockRumpsApp
    m.MenuItem = _MockMenuItem
    m.Timer = MagicMock(name="rumps.Timer")
    m.notification = MagicMock(name="rumps.notification")
    m.quit_application = MagicMock(name="rumps.quit_application")
    m.alert = MagicMock(name="rumps.alert")
    return m


def _make_foundation_module():
    m = types.ModuleType("Foundation")
    m.NSObject = _MockNSObject
    m.NSDistributedNotificationCenter = MagicMock(name="NSDistributedNotificationCenter")
    return m


def _make_appkit_module():
    m = types.ModuleType("AppKit")
    m.NSApplication = MagicMock(name="NSApplication")
    m.NSApplicationActivationPolicyProhibited = 2
    return m


_rumps = _make_rumps_module()
_foundation = _make_foundation_module()
_appkit = _make_appkit_module()

for _name, _mod in [("rumps", _rumps), ("Foundation", _foundation), ("AppKit", _appkit)]:
    sys.modules.setdefault(_name, _mod)

import eye_timer  # noqa: E402
from eye_timer import EyeTimerApp, ScreenObserver, TIPS  # noqa: E402

WORK_SEC = EyeTimerApp.WORK_SEC
REST_SEC = EyeTimerApp.REST_SEC


# ── Helper ────────────────────────────────────────────────────────────────────


def make_app():
    """Return a fresh EyeTimerApp with all mocks reset."""
    _rumps.Timer.reset_mock()
    _rumps.Timer.return_value = MagicMock(name="ticker")
    _rumps.notification.reset_mock()
    _rumps.alert.reset_mock()
    _foundation.NSDistributedNotificationCenter.reset_mock()
    return EyeTimerApp()


def _notification_kwarg(mock_call, key):
    """Extract a keyword arg from a rumps.notification() mock call."""
    return mock_call.kwargs.get(key, "")


# ── Tests ─────────────────────────────────────────────────────────────────────


class TestModuleConstants(unittest.TestCase):
    def test_work_seconds(self):
        self.assertEqual(EyeTimerApp.WORK_SEC, 1200)

    def test_rest_seconds(self):
        self.assertEqual(EyeTimerApp.REST_SEC, 20)

    def test_five_tips(self):
        self.assertEqual(len(TIPS), 5)

    def test_tips_are_nonempty_strings(self):
        for tip in TIPS:
            self.assertIsInstance(tip, str)
            self.assertTrue(tip)


class TestInitialState(unittest.TestCase):
    def setUp(self):
        self.app = make_app()

    def test_remaining_equals_work_duration(self):
        self.assertEqual(self.app.remaining, WORK_SEC)

    def test_mode_is_work(self):
        self.assertEqual(self.app.mode, "work")

    def test_auto_starts_on_launch(self):
        self.assertTrue(self.app.running)

    def test_break_counter_starts_at_zero(self):
        self.assertEqual(self.app.breaks, 0)

    def test_ticker_is_started(self):
        self.app._ticker.start.assert_called()


class TestTickCountdown(unittest.TestCase):
    def setUp(self):
        self.app = make_app()

    def test_tick_decrements_remaining_by_one(self):
        before = self.app.remaining
        self.app._tick(None)
        self.assertEqual(self.app.remaining, before - 1)

    def test_tick_does_not_change_mode_mid_cycle(self):
        self.app._tick(None)
        self.assertEqual(self.app.mode, "work")

    def test_remaining_never_goes_negative(self):
        self.app.remaining = 1
        self.app._tick(None)  # remaining → 0, triggers transition
        self.app._tick(None)  # first tick of rest phase
        self.assertGreaterEqual(self.app.remaining, 0)


class TestWorkToRestTransition(unittest.TestCase):
    """When the work countdown reaches 0, the app should switch to rest mode."""

    def setUp(self):
        self.app = make_app()
        _rumps.notification.reset_mock()
        self.app.remaining = 0
        self.app._tick(None)

    def test_mode_becomes_rest(self):
        self.assertEqual(self.app.mode, "rest")

    def test_remaining_set_to_rest_duration(self):
        self.assertEqual(self.app.remaining, REST_SEC)

    def test_break_counter_increments(self):
        self.assertEqual(self.app.breaks, 1)

    def test_breaks_item_title_updated(self):
        self.assertEqual(self.app.breaks_item.title, "Breaks today: 1")

    def test_break_notification_fired(self):
        _rumps.notification.assert_called_once()

    def test_break_notification_title_mentions_break(self):
        title = _notification_kwarg(_rumps.notification.call_args, "title")
        self.assertIn("break", title.lower())

    def test_break_notification_message_is_a_tip(self):
        message = _notification_kwarg(_rumps.notification.call_args, "message")
        self.assertIn(message, TIPS)


class TestRestToWorkTransition(unittest.TestCase):
    """When the rest countdown reaches 0, the app should return to work mode."""

    def setUp(self):
        self.app = make_app()
        self.app.mode = "rest"
        self.app.remaining = 0
        self.app.breaks = 3
        _rumps.notification.reset_mock()
        self.app._tick(None)

    def test_mode_becomes_work(self):
        self.assertEqual(self.app.mode, "work")

    def test_remaining_set_to_work_duration(self):
        self.assertEqual(self.app.remaining, WORK_SEC)

    def test_break_counter_unchanged(self):
        self.assertEqual(self.app.breaks, 3)

    def test_return_notification_fired(self):
        _rumps.notification.assert_called_once()

    def test_return_notification_message_includes_break_count(self):
        message = _notification_kwarg(_rumps.notification.call_args, "message")
        self.assertIn("3", message)


class TestTipsCycling(unittest.TestCase):
    """Tips should cycle through all 5 entries in order, then wrap."""

    def setUp(self):
        self.app = make_app()

    def _trigger_break(self):
        """Fire one work→rest transition and return the tip used."""
        _rumps.notification.reset_mock()
        self.app.remaining = 0
        self.app.mode = "work"
        self.app._tick(None)
        return _notification_kwarg(_rumps.notification.call_args, "message")

    def test_first_five_tips_match_tips_list(self):
        tips_seen = [self._trigger_break() for _ in range(5)]
        self.assertEqual(tips_seen, TIPS)

    def test_sixth_break_wraps_to_first_tip(self):
        self.app.breaks = 5  # next increment makes it 6 → index 5 % 5 = 0
        tip = self._trigger_break()
        self.assertEqual(tip, TIPS[0])


class TestStartPause(unittest.TestCase):
    def setUp(self):
        self.app = make_app()

    def test_pause_sets_running_false(self):
        self.app._pause()
        self.assertFalse(self.app.running)

    def test_pause_stops_ticker(self):
        self.app._ticker.stop.reset_mock()
        self.app._pause()
        self.app._ticker.stop.assert_called_once()

    def test_pause_updates_toggle_button_to_resume(self):
        self.app._pause()
        self.assertIn("Resume", self.app.toggle_btn.title)

    def test_start_sets_running_true(self):
        self.app._pause()
        self.app._start()
        self.assertTrue(self.app.running)

    def test_start_starts_ticker(self):
        self.app._ticker.start.reset_mock()
        self.app._start()
        self.app._ticker.start.assert_called()

    def test_start_updates_toggle_button_to_pause(self):
        self.app._pause()
        self.app._start()
        self.assertIn("Pause", self.app.toggle_btn.title)


class TestResetState(unittest.TestCase):
    def setUp(self):
        self.app = make_app()
        self.app.mode = "rest"
        self.app.remaining = 5
        self.app.breaks = 7
        self.app._reset_state()

    def test_mode_reset_to_work(self):
        self.assertEqual(self.app.mode, "work")

    def test_remaining_reset_to_full_work_duration(self):
        self.assertEqual(self.app.remaining, WORK_SEC)

    def test_breaks_zeroed(self):
        # _reset_state is a full session reset, not just a cycle reset
        self.assertEqual(self.app.breaks, 0)

    def test_running_set_false(self):
        self.assertFalse(self.app.running)

    def test_ticker_stopped(self):
        self.app._ticker.stop.assert_called()

    def test_breaks_item_title_reset(self):
        self.assertEqual(self.app.breaks_item.title, "Breaks today: 0")


class TestToggle(unittest.TestCase):
    def setUp(self):
        self.app = make_app()

    def test_toggle_pauses_a_running_timer(self):
        self.assertTrue(self.app.running)
        self.app.toggle(None)
        self.assertFalse(self.app.running)

    def test_toggle_resumes_a_paused_timer(self):
        self.app._pause()
        self.app.toggle(None)
        self.assertTrue(self.app.running)

    def test_double_toggle_leaves_timer_running(self):
        self.app.toggle(None)
        self.app.toggle(None)
        self.assertTrue(self.app.running)


class TestReset(unittest.TestCase):
    def setUp(self):
        self.app = make_app()
        self.app.mode = "rest"
        self.app.remaining = 5
        self.app.breaks = 3
        self.app.reset(None)

    def test_mode_is_work_after_reset(self):
        self.assertEqual(self.app.mode, "work")

    def test_remaining_is_full_after_reset(self):
        self.assertEqual(self.app.remaining, WORK_SEC)

    def test_breaks_zeroed_after_reset(self):
        self.assertEqual(self.app.breaks, 0)

    def test_timer_running_after_reset(self):
        self.assertTrue(self.app.running)


class TestScreenLock(unittest.TestCase):
    def setUp(self):
        self.app = make_app()

    def test_lock_pauses_a_running_timer(self):
        self.assertTrue(self.app.running)
        self.app.on_screen_lock()
        self.assertFalse(self.app.running)

    def test_lock_is_silent_when_already_paused(self):
        self.app._pause()
        self.app._ticker.stop.reset_mock()
        self.app.on_screen_lock()
        self.app._ticker.stop.assert_not_called()

    def test_lock_shows_pause_indicator_in_title(self):
        self.app.on_screen_lock()
        self.assertIn("⏸", self.app.title)

    def test_lock_updates_status_item_text(self):
        self.app.on_screen_lock()
        self.assertIn("locked", self.app.status_item.title.lower())


class TestScreenUnlock(unittest.TestCase):
    def setUp(self):
        self.app = make_app()
        self.app.mode = "rest"
        self.app.remaining = 5
        self.app.breaks = 4
        _rumps.notification.reset_mock()
        self.app.on_screen_unlock()

    def test_unlock_resets_to_work_mode(self):
        self.assertEqual(self.app.mode, "work")

    def test_unlock_restores_full_work_duration(self):
        self.assertEqual(self.app.remaining, WORK_SEC)

    def test_unlock_zeroes_break_counter(self):
        self.assertEqual(self.app.breaks, 0)

    def test_unlock_resumes_the_timer(self):
        self.assertTrue(self.app.running)

    def test_unlock_fires_welcome_back_notification(self):
        _rumps.notification.assert_called_once()

    def test_unlock_notification_is_welcome_back(self):
        title = _notification_kwarg(_rumps.notification.call_args, "title")
        self.assertIn("Welcome", title)


class TestUpdateDisplay(unittest.TestCase):
    def setUp(self):
        self.app = make_app()

    def test_work_title_shows_eye_emoji_and_time(self):
        self.app.mode = "work"
        self.app.remaining = 754  # 12 min 34 sec
        self.app._update_display()
        self.assertIn("👁", self.app.title)
        self.assertIn("12:34", self.app.title)

    def test_work_title_zero_pads_minutes_and_seconds(self):
        self.app.mode = "work"
        self.app.remaining = 65  # 1 min 5 sec
        self.app._update_display()
        self.assertIn("01:05", self.app.title)

    def test_work_title_at_full_twenty_minutes(self):
        self.app.mode = "work"
        self.app.remaining = 1200
        self.app._update_display()
        self.assertIn("20:00", self.app.title)

    def test_work_status_item_mentions_break(self):
        self.app.mode = "work"
        self.app.remaining = 754
        self.app._update_display()
        self.assertIn("12:34", self.app.status_item.title)
        self.assertIn("break", self.app.status_item.title.lower())

    def test_rest_title_shows_plant_emoji_and_seconds(self):
        self.app.mode = "rest"
        self.app.remaining = 15
        self.app._update_display()
        self.assertIn("🌿", self.app.title)
        self.assertIn("15", self.app.title)

    def test_rest_status_item_instructs_to_look_away(self):
        self.app.mode = "rest"
        self.app.remaining = 15
        self.app._update_display()
        self.assertIn("15", self.app.status_item.title)
        self.assertIn("away", self.app.status_item.title.lower())


class TestAbout(unittest.TestCase):
    def setUp(self):
        self.app = make_app()

    def test_about_opens_alert(self):
        self.app.about(None)
        _rumps.alert.assert_called_once()

    def test_about_alert_mentions_20_20_20(self):
        self.app.about(None)
        all_text = str(_rumps.alert.call_args)
        self.assertIn("20", all_text)


class TestScreenObserver(unittest.TestCase):
    def setUp(self):
        self.observer = ScreenObserver.new()
        self.mock_app = MagicMock()
        self.observer.setApp_(self.mock_app)

    def test_set_app_stores_reference(self):
        self.assertIs(self.observer._app, self.mock_app)

    def test_handle_lock_delegates_to_app(self):
        self.observer.handleLock_(None)
        self.mock_app.on_screen_lock.assert_called_once()

    def test_handle_unlock_delegates_to_app(self):
        self.observer.handleUnlock_(None)
        self.mock_app.on_screen_unlock.assert_called_once()


class TestObserverRegistration(unittest.TestCase):
    """EyeTimerApp.__init__ should register for both lock and unlock events."""

    def setUp(self):
        self.app = make_app()
        self.nc = _foundation.NSDistributedNotificationCenter.defaultCenter()

    def _registered_event_names(self):
        return [c.args[2] for c in self.nc.addObserver_selector_name_object_.call_args_list]

    def test_registers_for_screen_lock(self):
        self.assertIn("com.apple.screenIsLocked", self._registered_event_names())

    def test_registers_for_screen_unlock(self):
        self.assertIn("com.apple.screenIsUnlocked", self._registered_event_names())

    def test_exactly_two_observers_registered(self):
        self.assertEqual(len(self._registered_event_names()), 2)


if __name__ == "__main__":
    unittest.main()

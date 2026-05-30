"""
py2app build configuration for 20-20-20 Eye Timer.

Usage:
    pip install py2app
    python setup_app.py py2app

Output: dist/Eye Timer.app
"""

from setuptools import setup

APP = ["eye_timer.py"]
APP_NAME = "Eye Timer"
VERSION = "1.0.0"

OPTIONS = {
    "argv_emulation": False,        # Must be False for menu bar apps
    "plist": {
        "CFBundleName":             APP_NAME,
        "CFBundleDisplayName":      APP_NAME,
        "CFBundleIdentifier":       "app.eyetimer.eyetimer",
        "CFBundleVersion":          VERSION,
        "CFBundleShortVersionString": VERSION,
        "NSHumanReadableCopyright": "© 2026 Sandeep Arcot",

        # Hide from Dock — menu bar only
        "LSUIElement": True,

        # Notifications permission
        "NSUserNotificationAlertStyle": "alert",

        # Minimum macOS version
        "LSMinimumSystemVersion": "12.0",
    },
    "packages": ["rumps", "Foundation"],
    "includes": ["objc"],
    "frameworks": [],
    "resources": [],
    # Strip debug symbols for smaller binary
    "strip": True,
}

setup(
    name=APP_NAME,
    app=APP,
    version=VERSION,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)

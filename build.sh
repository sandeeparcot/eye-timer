#!/bin/bash
# ── Eye Timer — build & distribute ───────────────────────────────────────────
# Builds a signed, notarised .app and wraps it in a .dmg ready for sale.
#
# Prerequisites:
#   - Apple Developer account (developer.apple.com) — £79/yr
#   - Xcode Command Line Tools: xcode-select --install
#   - create-dmg: brew install create-dmg
#
# Usage:
#   chmod +x build.sh
#   ./build.sh
# ─────────────────────────────────────────────────────────────────────────────

set -e

APP_NAME="Eye Timer"
BUNDLE_ID="com.yourdomain.eyetimer"
VERSION="1.0.0"
DIST_DIR="dist"
DMG_NAME="EyeTimer-${VERSION}.dmg"

# ── Optional: set your Apple Developer identity here ─────────────────────────
# Find yours with: security find-identity -v -p codesigning
DEVELOPER_ID=""   # e.g. "Developer ID Application: Your Name (XXXXXXXXXX)"
APPLE_ID=""       # e.g. "you@example.com"  (for notarisation)
TEAM_ID=""        # e.g. "XXXXXXXXXX"

# ─────────────────────────────────────────────────────────────────────────────

echo "📦  Installing build dependencies..."
pip3 install py2app rumps pyobjc-framework-Cocoa --quiet

echo ""
echo "🔨  Building .app bundle..."
python3 setup_app.py py2app --quiet

APP_PATH="${DIST_DIR}/${APP_NAME}.app"

if [[ ! -d "$APP_PATH" ]]; then
  echo "❌  Build failed — $APP_PATH not found."
  exit 1
fi

echo "✅  Built: $APP_PATH"

# ── Code signing (requires Apple Developer account) ──────────────────────────
if [[ -n "$DEVELOPER_ID" ]]; then
  echo ""
  echo "🔏  Signing app..."
  codesign --force --deep --sign "$DEVELOPER_ID" \
    --options runtime \
    --entitlements entitlements.plist \
    "$APP_PATH"
  echo "✅  Signed."
else
  echo ""
  echo "⚠️   Skipping code signing — set DEVELOPER_ID in this script to sign."
  echo "    Without signing, macOS will warn users about an unidentified developer."
fi

# ── Create DMG ────────────────────────────────────────────────────────────────
if command -v create-dmg &>/dev/null; then
  echo ""
  echo "💿  Creating DMG..."
  create-dmg \
    --volname "$APP_NAME" \
    --volicon "icon.icns" \
    --window-pos 200 120 \
    --window-size 600 400 \
    --icon-size 128 \
    --icon "${APP_NAME}.app" 150 185 \
    --hide-extension "${APP_NAME}.app" \
    --app-drop-link 450 185 \
    "$DMG_NAME" \
    "$DIST_DIR/"
  echo "✅  DMG created: $DMG_NAME"
else
  echo "⚠️   create-dmg not found. Install with: brew install create-dmg"
  echo "    Distributable app is at: $APP_PATH"
fi

# ── Notarisation (requires Apple Developer account) ──────────────────────────
if [[ -n "$APPLE_ID" && -n "$TEAM_ID" && -f "$DMG_NAME" ]]; then
  echo ""
  echo "🍎  Submitting for notarisation (this takes 2–5 minutes)..."
  xcrun notarytool submit "$DMG_NAME" \
    --apple-id "$APPLE_ID" \
    --team-id "$TEAM_ID" \
    --wait
  xcrun stapler staple "$DMG_NAME"
  echo "✅  Notarised and stapled. Ready to distribute."
else
  echo ""
  echo "⚠️   Skipping notarisation — set APPLE_ID and TEAM_ID to notarise."
fi

echo ""
echo "─────────────────────────────────────────────────────────────────────────"
echo "🎉  Done!"
echo ""
echo "Distributable: ${DMG_NAME:-$APP_PATH}"
echo ""
echo "Next steps:"
echo "  1. Upload DMG to Gumroad (gumroad.com) and set your price"
echo "  2. Share your landing page link"
echo "─────────────────────────────────────────────────────────────────────────"

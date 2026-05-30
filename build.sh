#!/bin/bash
# ── Eye Timer — build & distribute ───────────────────────────────────────────
# Builds a signed, notarised .app and wraps it in a .dmg ready to distribute.
#
# Prerequisites:
#   - macOS with Xcode Command Line Tools: xcode-select --install
#   - Python 3.9+
#   - (optional) Apple Developer account for signing & notarisation
#   - (optional) create-dmg for a prettier DMG: brew install create-dmg
#
# Usage:
#   chmod +x build.sh
#   ./build.sh
# ─────────────────────────────────────────────────────────────────────────────

set -e

APP_NAME="Eye Timer"
VERSION="1.0.0"
DIST_DIR="dist"
DMG_NAME="EyeTimer-${VERSION}.dmg"
APP_PATH="${DIST_DIR}/${APP_NAME}.app"

# ── Optional: fill in your Apple Developer credentials ───────────────────────
# Find DEVELOPER_ID with: security find-identity -v -p codesigning
DEVELOPER_ID=""   # e.g. "Developer ID Application: Sandeep Arcot (XXXXXXXXXX)"
APPLE_ID=""       # e.g. "sandeep@example.com"
TEAM_ID=""        # e.g. "XXXXXXXXXX"
# ─────────────────────────────────────────────────────────────────────────────

echo "📦  Installing build dependencies..."
pip3 install py2app rumps pyobjc-framework-Cocoa --quiet

echo ""
echo "🔨  Building .app bundle..."
# Clean previous build artefacts so py2app doesn't reuse stale files
rm -rf build/ dist/
python3 setup_app.py py2app

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
  codesign --verify --deep --strict "$APP_PATH"
  echo "✅  Signed and verified."
else
  echo ""
  echo "⚠️   Skipping code signing — set DEVELOPER_ID to sign."
  echo "    Without signing, macOS shows an 'unidentified developer' warning."
fi

# ── Create DMG ────────────────────────────────────────────────────────────────
echo ""
if command -v create-dmg &>/dev/null; then
  echo "💿  Creating DMG with create-dmg..."
  CREATE_DMG_ARGS=(
    --volname "$APP_NAME"
    --window-pos 200 120
    --window-size 600 400
    --icon-size 128
    --icon "${APP_NAME}.app" 150 185
    --hide-extension "${APP_NAME}.app"
    --app-drop-link 450 185
  )
  # Only add a volume icon if one exists in the repo
  if [[ -f "icon.icns" ]]; then
    CREATE_DMG_ARGS+=(--volicon "icon.icns")
  fi
  create-dmg "${CREATE_DMG_ARGS[@]}" "$DMG_NAME" "$DIST_DIR/"
  echo "✅  DMG created: $DMG_NAME"
else
  echo "💿  create-dmg not found — falling back to hdiutil..."
  # Create a plain DMG using the macOS built-in tool (no Homebrew needed)
  STAGING_DIR="$(mktemp -d)"
  cp -r "$APP_PATH" "$STAGING_DIR/"
  ln -s /Applications "$STAGING_DIR/Applications"
  hdiutil create \
    -volname "$APP_NAME" \
    -srcfolder "$STAGING_DIR" \
    -ov \
    -format UDZO \
    "$DMG_NAME"
  rm -rf "$STAGING_DIR"
  echo "✅  DMG created: $DMG_NAME"
  echo "   (Install create-dmg for a prettier DMG: brew install create-dmg)"
fi

# ── Notarisation (requires Apple Developer account) ──────────────────────────
if [[ -n "$APPLE_ID" && -n "$TEAM_ID" ]]; then
  if [[ ! -f "$DMG_NAME" ]]; then
    echo "❌  DMG not found — cannot notarise."
    exit 1
  fi
  echo ""
  echo "🍎  Submitting for notarisation (takes 2–5 minutes)..."
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

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo "─────────────────────────────────────────────────────────────────────────"
echo "🎉  Done!"
echo ""
if [[ -f "$DMG_NAME" ]]; then
  echo "  Distributable DMG : $DMG_NAME"
  echo "  Size              : $(du -sh "$DMG_NAME" | cut -f1)"
else
  echo "  Distributable app : $APP_PATH"
fi
echo "─────────────────────────────────────────────────────────────────────────"

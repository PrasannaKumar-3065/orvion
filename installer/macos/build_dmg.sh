#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
#  Orvion  —  macOS DMG builder
#
#  Expects to run from the repository root AFTER `pyinstaller orvion.spec`.
#
#  Output:  dist/installer/Orvion-macos-universal.dmg
#
#  Optional env vars:
#    APPLE_IDENTITY    — Developer ID Application: ... (for notarisation)
#    APPLE_TEAM_ID     — 10-char Apple Team ID
#    APPLE_ID          — Apple ID email (notarytool)
#    APPLE_APP_PWD     — App-specific password (notarytool)
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
APP_BUNDLE="${REPO_ROOT}/dist/Orvion.app"
OUT_DIR="${REPO_ROOT}/dist/installer"
DMG_OUT="${OUT_DIR}/Orvion-macos-universal.dmg"
VERSION="${ORVION_VERSION:-1.0.0}"
ENTITLEMENTS="${REPO_ROOT}/installer/macos/entitlements.plist"
BACKGROUND="${REPO_ROOT}/installer/macos/dmg_background.png"  # optional

echo "━━━━  Orvion macOS DMG Builder  ━━━━"
echo "  App bundle : ${APP_BUNDLE}"
echo "  Output     : ${DMG_OUT}"
echo ""

# ── Sanity check ──────────────────────────────────────────────────────────────
if [ ! -d "${APP_BUNDLE}" ]; then
    echo "ERROR: ${APP_BUNDLE} not found."
    echo "  Run: pyinstaller orvion.spec --clean --noconfirm"
    exit 1
fi

mkdir -p "${OUT_DIR}"

# ── Install create-dmg if not present ────────────────────────────────────────
if ! command -v create-dmg &>/dev/null; then
    echo "→ Installing create-dmg via Homebrew…"
    brew install create-dmg
fi

# ── Code-sign (optional — only if APPLE_IDENTITY is set) ─────────────────────
if [ -n "${APPLE_IDENTITY:-}" ]; then
    echo "→ Code-signing ${APP_BUNDLE}…"
    codesign \
        --deep \
        --force \
        --verify \
        --verbose \
        --timestamp \
        --options runtime \
        --entitlements "${ENTITLEMENTS}" \
        --sign "${APPLE_IDENTITY}" \
        "${APP_BUNDLE}"
    echo "  ✓ Code-signed"
else
    echo "  ℹ  APPLE_IDENTITY not set — skipping code-signing."
fi

# ── Create DMG ────────────────────────────────────────────────────────────────
echo "→ Building DMG…"

# Remove previous attempt
rm -f "${DMG_OUT}"

CREATE_DMG_ARGS=(
    --volname   "Orvion ${VERSION}"
    --window-pos  200 120
    --window-size 620 400
    --icon-size   128
    --icon        "Orvion.app" 180 170
    --hide-extension "Orvion.app"
    --app-drop-link  430 170
    --no-internet-enable
)

# Attach background if present
if [ -f "${BACKGROUND}" ]; then
    CREATE_DMG_ARGS+=(--background "${BACKGROUND}")
fi

create-dmg "${CREATE_DMG_ARGS[@]}" "${DMG_OUT}" "${APP_BUNDLE}"

echo ""
echo "✅  DMG created: ${DMG_OUT}"
echo "    Size: $(du -sh "${DMG_OUT}" | cut -f1)"

# ── Notarise (optional — only if Apple credentials are set) ──────────────────
if [ -n "${APPLE_ID:-}" ] && [ -n "${APPLE_APP_PWD:-}" ] && [ -n "${APPLE_TEAM_ID:-}" ]; then
    echo ""
    echo "→ Submitting for notarisation…"
    xcrun notarytool submit "${DMG_OUT}" \
        --apple-id    "${APPLE_ID}" \
        --password    "${APPLE_APP_PWD}" \
        --team-id     "${APPLE_TEAM_ID}" \
        --wait

    echo "→ Stapling ticket…"
    xcrun stapler staple "${DMG_OUT}"
    echo "  ✓ Notarised and stapled"
else
    echo "  ℹ  Apple credentials not set — skipping notarisation."
fi

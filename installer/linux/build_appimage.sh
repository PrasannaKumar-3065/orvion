#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
#  Orvion  —  Linux AppImage builder
#
#  Expects to run from the repository root AFTER `pyinstaller orvion.spec`.
#
#  Output:  dist/installer/Orvion-linux-x86_64.AppImage
#
#  Dependencies (auto-downloaded if missing):
#    • appimagetool  — https://github.com/AppImage/AppImageKit
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
DIST_DIR="${REPO_ROOT}/dist/Orvion"
APPDIR="${REPO_ROOT}/dist/Orvion.AppDir"
OUT_DIR="${REPO_ROOT}/dist/installer"
APPIMAGE_TOOL="${REPO_ROOT}/dist/appimagetool-x86_64.AppImage"
VERSION="${ORVION_VERSION:-1.0.0}"

echo "━━━━  Orvion Linux AppImage Builder  ━━━━"
echo "  Repo root : ${REPO_ROOT}"
echo "  Dist dir  : ${DIST_DIR}"
echo "  AppDir    : ${APPDIR}"
echo "  Output    : ${OUT_DIR}"
echo ""

# ── Sanity check ──────────────────────────────────────────────────────────────
if [ ! -d "${DIST_DIR}" ]; then
    echo "ERROR: ${DIST_DIR} does not exist."
    echo "  Run: pyinstaller orvion.spec --clean --noconfirm"
    exit 1
fi

# ── Download appimagetool if needed ───────────────────────────────────────────
if [ ! -f "${APPIMAGE_TOOL}" ]; then
    echo "→ Downloading appimagetool…"
    curl -sSL \
      "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage" \
      -o "${APPIMAGE_TOOL}"
    chmod +x "${APPIMAGE_TOOL}"
fi

# ── Build AppDir structure ────────────────────────────────────────────────────
echo "→ Building AppDir…"
rm -rf "${APPDIR}"
mkdir -p "${APPDIR}/usr/bin"
mkdir -p "${APPDIR}/usr/share/applications"
mkdir -p "${APPDIR}/usr/share/icons/hicolor/256x256/apps"

# Copy PyInstaller bundle
cp -r "${DIST_DIR}/." "${APPDIR}/usr/bin/"

# AppRun entry script
cp "${REPO_ROOT}/installer/linux/AppRun" "${APPDIR}/AppRun"
chmod +x "${APPDIR}/AppRun"

# .desktop file (must be at root of AppDir)
cp "${REPO_ROOT}/installer/linux/orvion.desktop" "${APPDIR}/orvion.desktop"
cp "${REPO_ROOT}/installer/linux/orvion.desktop" \
   "${APPDIR}/usr/share/applications/orvion.desktop"

# Icon (AppImage requires icon at root AND in hicolor tree)
if [ -f "${REPO_ROOT}/installer/linux/orvion.png" ]; then
    cp "${REPO_ROOT}/installer/linux/orvion.png" "${APPDIR}/orvion.png"
    cp "${REPO_ROOT}/installer/linux/orvion.png" \
       "${APPDIR}/usr/share/icons/hicolor/256x256/apps/orvion.png"
else
    echo "  WARN: installer/linux/orvion.png not found — AppImage will lack icon."
    # Create a minimal 1×1 placeholder so appimagetool does not error
    python3 -c "
from PIL import Image
img = Image.new('RGBA', (256, 256), (108, 78, 230, 255))
img.save('${APPDIR}/orvion.png')
" 2>/dev/null || touch "${APPDIR}/orvion.png"
    cp "${APPDIR}/orvion.png" \
       "${APPDIR}/usr/share/icons/hicolor/256x256/apps/orvion.png"
fi

# Fix executable bit on the main binary
chmod +x "${APPDIR}/usr/bin/Orvion"

# ── Patch the bundled AppRun to point to the correct binary ───────────────────
# The PyInstaller binary lives at usr/bin/Orvion inside AppDir
sed -i 's|exec "${HERE}/Orvion"|exec "${HERE}/usr/bin/Orvion"|' "${APPDIR}/AppRun"

# ── Build the AppImage ────────────────────────────────────────────────────────
mkdir -p "${OUT_DIR}"
OUTPUT="${OUT_DIR}/Orvion-linux-x86_64.AppImage"

echo "→ Running appimagetool…"
# ARCH must be set for appimagetool
ARCH=x86_64 "${APPIMAGE_TOOL}" \
    --comp gzip \
    "${APPDIR}" \
    "${OUTPUT}"

echo ""
echo "✅  AppImage created: ${OUTPUT}"
echo "    Size: $(du -sh "${OUTPUT}" | cut -f1)"

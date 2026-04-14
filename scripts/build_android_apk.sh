#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ANDROID_DIR="$ROOT_DIR/mobile/android-dashboard"

if [[ -z "${ANDROID_HOME:-}" && -z "${ANDROID_SDK_ROOT:-}" ]]; then
  echo "ERROR: define ANDROID_HOME or ANDROID_SDK_ROOT before building APK."
  exit 1
fi

cd "$ANDROID_DIR"
gradle assembleDebug

echo "APK generated (if build succeeded):"
echo "  $ANDROID_DIR/app/build/outputs/apk/debug/app-debug.apk"

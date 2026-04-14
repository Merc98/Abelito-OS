#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ANDROID_DIR="$ROOT_DIR/mobile/android-dashboard"
SDK_ROOT_DEFAULT="$ROOT_DIR/.android-sdk"
CMDLINE_TOOLS_DIR="$SDK_ROOT_DEFAULT/cmdline-tools/latest"
SDKMANAGER_BIN="$CMDLINE_TOOLS_DIR/bin/sdkmanager"
TOOLS_ZIP_URL_PRIMARY="https://dl.google.com/android/repository/commandlinetools-linux-13114758_latest.zip"
TOOLS_ZIP_URL_FALLBACK="https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip"

bootstrap_cmdline_tools() {
  mkdir -p "$SDK_ROOT_DEFAULT/cmdline-tools"
  local zip_path="$ROOT_DIR/.android-cmdline-tools.zip"
  local unpack_dir="$ROOT_DIR/.android-cmdline-tools"
  rm -rf "$unpack_dir"
  rm -f "$zip_path"

  if ! curl -fsSL "$TOOLS_ZIP_URL_PRIMARY" -o "$zip_path"; then
    curl -fsSL "$TOOLS_ZIP_URL_FALLBACK" -o "$zip_path"
  fi

  mkdir -p "$unpack_dir"
  unzip -q "$zip_path" -d "$unpack_dir"
  rm -rf "$CMDLINE_TOOLS_DIR"
  mkdir -p "$SDK_ROOT_DEFAULT/cmdline-tools"
  mv "$unpack_dir/cmdline-tools" "$CMDLINE_TOOLS_DIR"
  rm -rf "$unpack_dir" "$zip_path"
}

export ANDROID_SDK_ROOT="${ANDROID_SDK_ROOT:-${ANDROID_HOME:-$SDK_ROOT_DEFAULT}}"
export ANDROID_HOME="$ANDROID_SDK_ROOT"

if [[ ! -x "$SDKMANAGER_BIN" ]]; then
  echo "Bootstrapping Android command-line tools into $ANDROID_SDK_ROOT ..."
  bootstrap_cmdline_tools
fi

export PATH="$CMDLINE_TOOLS_DIR/bin:$ANDROID_SDK_ROOT/platform-tools:$PATH"

mkdir -p "$ANDROID_SDK_ROOT"
(
  set +o pipefail
  yes | "$SDKMANAGER_BIN" --sdk_root="$ANDROID_SDK_ROOT" --licenses >/dev/null
)
"$SDKMANAGER_BIN" --sdk_root="$ANDROID_SDK_ROOT" \
  "platform-tools" \
  "platforms;android-34" \
  "build-tools;34.0.0"

cd "$ANDROID_DIR"
cat > local.properties <<EOF
sdk.dir=$ANDROID_SDK_ROOT
EOF

gradle --no-daemon assembleDebug

echo "APK generated (if build succeeded):"
echo "  $ANDROID_DIR/app/build/outputs/apk/debug/app-debug.apk"

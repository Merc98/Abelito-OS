#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_DIR="$ROOT_DIR/dist"
VERSION="${1:-v1.0.0}"
BUNDLE="$DIST_DIR/abelito-os-${VERSION}.tar.gz"

mkdir -p "$DIST_DIR"
tar -czf "$BUNDLE" \
  -C "$ROOT_DIR" \
  README.md Makefile requirements.txt \
  apps core shared scripts mobile tests docs docker-compose.yml

echo "release_bundle_created=$BUNDLE"

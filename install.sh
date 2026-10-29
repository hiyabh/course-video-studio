#!/usr/bin/env bash
#
# Install the course-video-studio skill into ~/.claude/skills/
#
#   curl -fsSL https://hiyabh.github.io/course-video-studio/install.sh | bash
#   curl -fsSL https://hiyabh.github.io/course-video-studio/install.sh | bash -s -- --update   (replace an older copy)
#
set -euo pipefail

BASE="${SKILL_BASE:-https://hiyabh.github.io/course-video-studio}"   # override only for local testing
NAME="course-video-studio"
DEST="${HOME}/.claude/skills/${NAME}"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

if [ -e "$DEST" ] && [ "${1:-}" != "--update" ]; then
  echo "skip: $DEST already exists. To replace it with the latest version run again with --update"
  exit 0
fi

if command -v curl >/dev/null 2>&1; then curl -fsSL "$BASE/$NAME.tar.gz" -o "$TMP/pkg.tar.gz"
elif command -v wget >/dev/null 2>&1; then wget -q "$BASE/$NAME.tar.gz" -O "$TMP/pkg.tar.gz"
else echo "ERROR: neither curl nor wget is available." >&2; exit 1
fi

tar -xzf "$TMP/pkg.tar.gz" -C "$TMP"
mkdir -p "$(dirname "$DEST")"
rm -rf "$DEST"
cp -r "$TMP/$NAME" "$DEST"
echo "ok: $NAME installed in $DEST ($(cat "$DEST/VERSION" 2>/dev/null || echo unknown version))"
echo "Restart Claude Code, then ask it: תבנה לי קורס וידאו על ..."

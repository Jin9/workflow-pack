#!/usr/bin/env bash
set -euo pipefail

# ---- Configuration ----
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_DIR="$SCRIPT_DIR/project-skeleton"
OUTPUT_DIR="$SCRIPT_DIR/generated"

MODULE_PREFIX="gitlab.com/example-org/platform/backend"
OLD_NAME="project-skeleton"

# Canonical skill synced into every generated repo so they carry the latest
# version rather than the skeleton's embedded snapshot.
SKILL_SRC="$SCRIPT_DIR/skills/implementing-go-template-requirements"
SKILL_DEST_REL=".github/skills/implementing-go-template-requirements"

# Edit this list to add/remove projects you want generated.
PROJECTS=(
  "promo-service"
)

# CLI args override the hardcoded list for this run only.
if [ "$#" -gt 0 ]; then
  PROJECTS=("$@")
fi

# ---- Pre-flight ----
[ -d "$SOURCE_DIR" ] || { echo "ERROR: source not found: $SOURCE_DIR" >&2; exit 1; }
[ -d "$SKILL_SRC" ] || echo "[warn] canonical skill not found at $SKILL_SRC — generated repos will keep the skeleton's embedded skill snapshot" >&2
command -v go >/dev/null 2>&1 || { echo "ERROR: 'go' not found in PATH" >&2; exit 1; }
mkdir -p "$OUTPUT_DIR"

is_valid_name() {
  [[ "$1" =~ ^[a-z0-9]([a-z0-9-]*[a-z0-9])?$ ]]
}

# ---- Generation loop ----
created=0
skipped=0
invalid=0

for name in "${PROJECTS[@]}"; do
  if ! is_valid_name "$name"; then
    echo "[invalid] '$name': must be kebab-case (lowercase letters/digits/hyphens, no leading/trailing hyphen)" >&2
    invalid=$((invalid + 1))
    continue
  fi

  target="$OUTPUT_DIR/$name"
  if [ -e "$target" ]; then
    echo "[skip] $name: $target already exists"
    skipped=$((skipped + 1))
    continue
  fi

  # Copy the skeleton. Prefer rsync for clean --exclude handling; fall back to cp -R.
  if command -v rsync >/dev/null 2>&1; then
    rsync -a --exclude='.git' --exclude='.DS_Store' "$SOURCE_DIR/" "$target/"
  else
    cp -R "$SOURCE_DIR" "$target"
    rm -rf "$target/.git" 2>/dev/null || true
  fi

  # Rewrite the Go module path in every file that mentions the old name.
  # perl -i is portable across macOS BSD and Linux GNU (sed -i differs).
  files_to_edit=()
  while IFS= read -r f; do
    files_to_edit+=("$f")
  done < <(grep -RIl "${MODULE_PREFIX}/${OLD_NAME}" "$target" || true)

  if [ "${#files_to_edit[@]}" -gt 0 ]; then
    perl -pi -e "s|\\Q${MODULE_PREFIX}/${OLD_NAME}\\E|${MODULE_PREFIX}/${name}|g" "${files_to_edit[@]}"
  fi

  # Sync the canonical skill over the skeleton's embedded snapshot so the
  # generated repo carries the latest version. The skill is module-agnostic
  # (placeholder import paths), so it is copied AFTER the module-path rewrite
  # and needs no rewriting itself.
  if [ -d "$SKILL_SRC" ]; then
    rm -rf "$target/$SKILL_DEST_REL"
    mkdir -p "$(dirname "$target/$SKILL_DEST_REL")"
    if command -v rsync >/dev/null 2>&1; then
      rsync -a --exclude='.git' --exclude='.DS_Store' "$SKILL_SRC/" "$target/$SKILL_DEST_REL/"
    else
      cp -R "$SKILL_SRC" "$target/$SKILL_DEST_REL"
    fi
  fi

  # git init with `develop` as the default branch (no initial commit).
  # git >= 2.28 supports `-b`; older versions need symbolic-ref.
  if ! git -C "$target" init -b develop -q 2>/dev/null; then
    git -C "$target" init -q
    git -C "$target" symbolic-ref HEAD refs/heads/develop
  fi

  # Resolve dependencies. Assumes GOPRIVATE is configured globally for the
  # private module host (gitlab.com/example-org/platform/backend).
  # On failure, warn and continue — the repo is still usable, just needs a
  # manual `go mod tidy` after credentials/network are sorted.
  if ! (cd "$target" && go mod tidy); then
    echo "[warn] $name: 'go mod tidy' failed — repo created, run it manually after fixing credentials/network" >&2
  fi

  echo "[ok] $name: created at $target (branch: develop)"
  created=$((created + 1))
done

echo
echo "Summary: created=$created, skipped=$skipped, invalid=$invalid"

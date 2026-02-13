#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PAPER_DIR="$ROOT_DIR/tex/math_instantiation"
BUILD_DIR="$PAPER_DIR/build"
STAGE_DIR="$BUILD_DIR/preprints_source_staging"
ZIP_PATH="$BUILD_DIR/preprints_source_upload.zip"
MAIN_TEX="$PAPER_DIR/main.tex"
MAIN_BBL="$PAPER_DIR/main.bbl"

rm -rf "$STAGE_DIR"
mkdir -p "$STAGE_DIR/sections" "$STAGE_DIR/figures" "$STAGE_DIR/generated" "$STAGE_DIR/bib"

if [[ ! -f "$MAIN_TEX" ]]; then
  echo "[package_preprints] ERROR: missing $MAIN_TEX" >&2
  exit 2
fi

if [[ ! -f "$MAIN_BBL" ]]; then
  if command -v pdflatex >/dev/null 2>&1; then
    pdflatex -interaction=nonstopmode -halt-on-error -output-directory "$BUILD_DIR" "$MAIN_TEX" >/dev/null
    (cd "$BUILD_DIR" && bibtex main) >/dev/null || true
    cp -f "$BUILD_DIR/main.bbl" "$MAIN_BBL"
  else
    echo "[package_preprints] ERROR: missing main.bbl and pdflatex unavailable." >&2
    exit 3
  fi
fi

cp "$MAIN_TEX" "$STAGE_DIR/main.tex"
cp "$MAIN_BBL" "$STAGE_DIR/main.bbl"
cp "$PAPER_DIR/preamble.tex" "$STAGE_DIR/preamble.tex"
cp "$PAPER_DIR/bib/refs.bib" "$STAGE_DIR/bib/refs.bib"

if [[ -d "$PAPER_DIR/sections" ]]; then
  cp "$PAPER_DIR/sections/"*.tex "$STAGE_DIR/sections/" 2>/dev/null || true
fi
if [[ -d "$PAPER_DIR/generated" ]]; then
  cp "$PAPER_DIR/generated/"*.tex "$STAGE_DIR/generated/" 2>/dev/null || true
fi

if [[ -d "$PAPER_DIR/Definitions" ]]; then
  cp -r "$PAPER_DIR/Definitions" "$STAGE_DIR/Definitions"
fi

if [[ -d "$ROOT_DIR/figures" ]]; then
  mapfile -t FIG_FILES < <(
    python - "$PAPER_DIR" <<'PY'
import re
import sys
from pathlib import Path

paper_dir = Path(sys.argv[1])
paths = [paper_dir / "main.tex"] + sorted((paper_dir / "sections").glob("*.tex"))
pattern = re.compile(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}")
seen = []

for path in paths:
    if not path.exists():
        continue
    text = path.read_text(encoding="utf-8", errors="replace")
    for raw in pattern.findall(text):
        name = raw.strip()
        if not name:
            continue
        # Keep exact filename reference as used by TeX includegraphics.
        seen.append(Path(name).name)

for name in dict.fromkeys(seen):
    print(name)
PY
  )

  for fig in "${FIG_FILES[@]}"; do
    [[ -z "$fig" ]] && continue
    src="$ROOT_DIR/figures/$fig"
    if [[ ! -f "$src" ]]; then
      echo "[package_preprints] ERROR: referenced figure missing: $src" >&2
      exit 4
    fi
    cp "$src" "$STAGE_DIR/figures/"
  done
fi

find "$STAGE_DIR" -name "*.aux" -delete
find "$STAGE_DIR" -name "*.log" -delete
find "$STAGE_DIR" -name "*.out" -delete
find "$STAGE_DIR" -name "*.toc" -delete
find "$STAGE_DIR" -name ".DS_Store" -delete

rm -f "$ZIP_PATH"
pushd "$STAGE_DIR" >/dev/null
zip -r "$ZIP_PATH" . >/dev/null
popd >/dev/null

echo "[package_preprints] Wrote $ZIP_PATH"

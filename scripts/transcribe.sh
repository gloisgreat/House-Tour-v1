#!/usr/bin/env bash
# Usage: scripts/transcribe.sh raw/<clip>  ->  transcript/words.json (skips if it already exists)
set -euo pipefail
cd "$(dirname "$0")/.."
RAW="${1:?usage: scripts/transcribe.sh raw/<clip>}"
PY=~/.cache/video-editor/whisperx-venv/bin/python
if [ -s transcript/words.json ]; then echo "transcript/words.json exists, not re-transcribing"; exit 0; fi
ffmpeg -y -v error -i "$RAW" -vn -ac 1 -ar 16000 -c:a pcm_s16le transcript/audio16k.wav
"$PY" scripts/transcribe.py transcript/audio16k.wav transcript/words.json

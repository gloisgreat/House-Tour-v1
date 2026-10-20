# Video editor notes
- Finishing app: CapCut -> render ./cut.mp4 (scripts/render.py), user drags it into a new CapCut project.
- Runs in a Claude Code cloud container (Linux x86_64, 4 CPU, no GPU): WhisperX runs CPU int8. Raw footage arrives via git push to raw/.
- Pipeline: scripts/transcribe.sh raw/<clip> -> transcript/words.json; write transcript/cuts.json; python3 scripts/render.py raw/<clip>.

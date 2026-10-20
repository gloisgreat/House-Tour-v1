# Video editor notes
- Finishing app: CapCut -> render ./cut.mp4 (scripts/render.py), user drags it into a new CapCut project.
- Runs in a Claude Code cloud container (Linux x86_64, 4 CPU, no GPU): WhisperX runs CPU int8. Raw footage arrives via git push to raw/.
- Pipeline: scripts/transcribe.sh raw/<clip> -> transcript/words.json; write transcript/cuts.json; python3 scripts/render.py raw/<clip>.
- Footage lives as assets on the `Housev1` GitHub release (repo is private). `scripts/fetch_release.sh Housev1` pulls them into raw/ via the API and checks sha256; raw/*.mp4 is gitignored.
- Housev1 = 23 DJI Mimo "glamour" clips, 3-17 s each (~160 s total), 1728x3072 vertical, 30 fps, AAC 48k stereo. They are silent house-tour b-roll (exterior, entry, living, kitchen, office, stairs, baths, bedroom, balcony), not talking head: audio averages -42 to -67 dB.
- Review flow: `python3 scripts/render.py --preview --out preview.mp4` renders a small 360-wide draft of cuts.json (segments carry their own "file") so the user can see the cut before approving.

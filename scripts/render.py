"""Render transcript/cuts.json with one ffmpeg filtergraph, then verify the frame count.
Each segment may name its own "file"; otherwise the raw clip given on the command line is used.
Usage: python3 scripts/render.py [raw/<clip>] [--out cut.mp4] [--preview]
  --preview renders a small 360-wide draft for review instead of the full-size cut."""
import argparse, json, subprocess
from fractions import Fraction

ap = argparse.ArgumentParser()
ap.add_argument("raw", nargs="?")
ap.add_argument("--out", default="cut.mp4")
ap.add_argument("--preview", action="store_true")
args = ap.parse_args()

def probe(path, entries, extra=()):
    return json.loads(subprocess.check_output(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", *extra, "-show_entries", entries, "-of", "json", path]))

segs = json.load(open("transcript/cuts.json"))["segments"]
files = []
for s in segs:
    f = s.get("file", args.raw)
    if f not in files:
        files.append(f)
info = {f: probe(f, "stream=r_frame_rate,width,height,nb_frames")["streams"][0] for f in files}
fps = Fraction(info[files[0]]["r_frame_rate"])
size = {(i["width"], i["height"]) for i in info.values()}
assert all(Fraction(i["r_frame_rate"]) == fps for i in info.values()), "mixed frame rates"
assert len(size) == 1, f"mixed frame sizes {size}"
w, h = size.pop()

frames = []
for s in segs:
    f = s.get("file", args.raw)
    a, b = round(s["start"] * fps), round(s["end"] * fps)  # end exclusive
    assert 0 <= a < b <= int(info[f]["nb_frames"]), f"{f}: {s['start']}-{s['end']} outside clip"
    frames.append((files.index(f), a, b))
for i in range(1, len(frames)):  # pieces from the same clip must not overlap
    if frames[i][0] == frames[i - 1][0]:
        assert frames[i][1] >= frames[i - 1][2], f"overlap at piece {i}"

scale = ",scale=360:-2" if args.preview else ""
parts, labels = [], []
for i, (k, a, b) in enumerate(frames):
    parts.append(f"[{k}:v]trim=start_frame={a}:end_frame={b},setpts=PTS-STARTPTS{scale}[v{i}]")
    parts.append(f"[{k}:a]atrim=start={float(a / fps)}:end={float(b / fps)},asetpts=PTS-STARTPTS[a{i}]")
    labels.append(f"[v{i}][a{i}]")
parts.append("".join(labels) + f"concat=n={len(frames)}:v=1:a=1[v][a]")
enc = ["-crf", "28", "-preset", "veryfast", "-b:a", "96k"] if args.preview else ["-crf", "18", "-preset", "medium", "-b:a", "192k"]
inputs = [x for f in files for x in ("-i", f)]
subprocess.run(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", ";".join(parts),
                "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
                "-fps_mode", "passthrough", "-movflags", "+faststart", *enc, args.out], check=True)

want = sum(b - a for _, a, b in frames)
got = int(probe(args.out, "stream=nb_read_frames", ["-count_frames"])["streams"][0]["nb_read_frames"])
dur = float(json.loads(subprocess.check_output(
    ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", args.out]))["format"]["duration"])
print(f"source {w}x{h} @ {float(fps):.3f} fps, pieces={len(frames)}")
print(f"frames: expected {want}, got {got} -> {'OK' if want == got else 'MISMATCH'}")
print(f"duration: expected {float(want / fps):.3f}s, got {dur:.3f}s")

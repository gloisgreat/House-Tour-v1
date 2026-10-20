"""Render transcript/cuts.json from the raw clip to ./cut.mp4 with one filtergraph, then verify frames.
Usage: python3 scripts/render.py raw/<clip>"""
import json, subprocess, sys
from fractions import Fraction

raw = sys.argv[1]
def probe(path, entries, extra=()):
    return json.loads(subprocess.check_output(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", *extra, "-show_entries", entries, "-of", "json", path]))

s = probe(raw, "stream=r_frame_rate,width,height:stream_side_data=rotation")["streams"][0]
fps = Fraction(s["r_frame_rate"])
segs = json.load(open("transcript/cuts.json"))["segments"]
frames = [(round(x["start"] * fps), round(x["end"] * fps)) for x in segs]  # end exclusive
for i in range(1, len(frames)):
    assert frames[i][0] >= frames[i - 1][1], f"overlap at piece {i}"

parts, labels = [], []
for i, (a, b) in enumerate(frames):
    parts.append(f"[0:v]trim=start_frame={a}:end_frame={b},setpts=PTS-STARTPTS[v{i}]")
    parts.append(f"[0:a]atrim=start={float(a / fps)}:end={float(b / fps)},asetpts=PTS-STARTPTS[a{i}]")
    labels.append(f"[v{i}][a{i}]")
parts.append("".join(labels) + f"concat=n={len(frames)}:v=1:a=1[v][a]")
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", raw, "-filter_complex", ";".join(parts),
                "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-crf", "18", "-preset", "medium",
                "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-fps_mode", "passthrough",
                "-movflags", "+faststart", "cut.mp4"], check=True)

want = sum(b - a for a, b in frames)
got = int(probe("cut.mp4", "stream=nb_read_frames", ["-count_frames"])["streams"][0]["nb_read_frames"])
dur = float(json.loads(subprocess.check_output(
    ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", "cut.mp4"]))["format"]["duration"])
print(f"{s['width']}x{s['height']} @ {float(fps):.3f} fps, pieces={len(frames)}")
print(f"frames: expected {want}, got {got} -> {'OK' if want == got else 'MISMATCH'}")
print(f"duration: expected {float(want / fps):.3f}s, got {dur:.3f}s")

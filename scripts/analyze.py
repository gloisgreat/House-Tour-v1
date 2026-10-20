"""Per-clip shot analysis: roll tilt (from near-vertical lines) and camera motion, in 0.5 s bins.
Usage: ~/.cache/video-editor/tools-venv/bin/python scripts/analyze.py raw/*.mp4 > transcript/analysis.json"""
import json, sys
import cv2, numpy as np

def tilt(gray):
    edges = cv2.Canny(gray, 60, 160)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 720, 40, minLineLength=gray.shape[0] // 8, maxLineGap=6)
    if lines is None:
        return None
    angs, wts = [], []
    for x1, y1, x2, y2 in lines.reshape(-1, 4):
        dx, dy = x2 - x1, y2 - y1
        a = np.degrees(np.arctan2(dx, dy))  # 0 = vertical
        a = (a + 90) % 180 - 90
        if abs(a) < 12:
            angs.append(a); wts.append(np.hypot(dx, dy))
    if sum(wts) < gray.shape[0]:
        return None
    o = np.argsort(angs); c = np.cumsum(np.array(wts)[o])
    return float(np.array(angs)[o][np.searchsorted(c, c[-1] / 2)])  # length-weighted median

out = {}
for path in sys.argv[1:]:
    cap = cv2.VideoCapture(path); fps = cap.get(cv2.CAP_PROP_FPS)
    step = max(1, round(fps / 10)); prev = None; rows = []; i = 0
    while True:
        ok, f = cap.read()
        if not ok:
            break
        if i % step == 0:
            g = cv2.cvtColor(cv2.resize(f, (432, 768)), cv2.COLOR_BGR2GRAY)
            m = None
            if prev is not None:
                (dx, dy), _ = cv2.phaseCorrelate(np.float32(prev), np.float32(g))
                m = float(np.hypot(dx, dy))
            rows.append((i / fps, tilt(g), m)); prev = g
        i += 1
    bins = []
    for b in range(int(rows[-1][0] / 0.5) + 1):
        r = [x for x in rows if b * 0.5 <= x[0] < (b + 1) * 0.5]
        t = [x[1] for x in r if x[1] is not None]; m = [x[2] for x in r if x[2] is not None]
        bins.append({"t": b * 0.5, "tilt": round(float(np.median(t)), 2) if t else None,
                     "motion": round(float(np.mean(m)), 1) if m else None,
                     "jerk": round(float(np.std(np.diff(m))), 1) if len(m) > 2 else None})
    out[path] = {"fps": fps, "frames": i, "bins": bins}
    print(path, file=sys.stderr)
json.dump(out, sys.stdout, indent=0)

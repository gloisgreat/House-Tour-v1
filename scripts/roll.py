"""Camera roll from the vertical vanishing point (immune to up/down pitch keystone).
Usage: tools-venv python scripts/roll.py transcript/cuts.json  -> prints roll per segment at 5 sample times"""
import json, sys
import cv2, numpy as np

def roll(gray):
    h, w = gray.shape
    edges = cv2.Canny(gray, 60, 160)
    L = cv2.HoughLinesP(edges, 1, np.pi / 720, 40, minLineLength=h // 10, maxLineGap=6)
    if L is None:
        return None
    rows = []
    for x1, y1, x2, y2 in L.reshape(-1, 4):
        a = (np.degrees(np.arctan2(x2 - x1, y2 - y1)) + 90) % 180 - 90
        if abs(a) < 20:
            l = np.cross([x1 - w / 2, y1 - h / 2, w], [x2 - w / 2, y2 - h / 2, w]).astype(float)
            l /= np.hypot(l[0], l[1])
            rows.append((l, np.hypot(x2 - x1, y2 - y1)))
    if len(rows) < 4:
        return None
    ls = np.array([r[0] for r in rows]); ws = np.array([r[1] for r in rows])
    keep = np.ones(len(ls), bool)
    for _ in range(4):  # reweighted least squares for the vanishing point, dropping outliers
        M = (ls[keep] * ws[keep, None]).T @ ls[keep]
        v = np.linalg.eigh(M)[1][:, 0]
        r = np.abs(ls @ v) / max(np.linalg.norm(v[:2]), 1e-9) / w if abs(v[2]) > 1e-9 else np.abs(ls[:, :2] @ v[:2] / np.linalg.norm(v[:2]))
        keep = r < np.quantile(r, 0.7)
        if keep.sum() < 4:
            break
    d = np.array([v[0], v[1]])  # direction from image centre to the VP (centred coords, w-scaled)
    if d[1] < 0:
        d = -d
    return float(np.degrees(np.arctan2(d[0], d[1])))

segs = json.load(open(sys.argv[1]))["segments"]
for n, s in enumerate(segs, 1):
    cap = cv2.VideoCapture(s["file"]); fps = cap.get(cv2.CAP_PROP_FPS); vals = []
    for t in np.linspace(s["start"] + 0.05, s["end"] - 0.05, int(sys.argv[2]) if len(sys.argv) > 2 else 5):
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(t * fps)); ok, f = cap.read()
        vals.append(roll(cv2.cvtColor(cv2.resize(f, (540, 960)), cv2.COLOR_BGR2GRAY)) if ok else None)
    print(n, s["file"][22:28], " ".join(f"{x:6.2f}" if x is not None else "     -" for x in vals))

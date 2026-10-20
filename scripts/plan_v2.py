import json, glob, statistics
files = {f[22:28]: f for f in sorted(glob.glob("raw/*.mp4"))}
A = json.load(open("transcript/analysis.json"))
plan = [
 ("143618", 1.0, 4.0, "Exterior push-in"),
 ("143756", 1.5, 3.5, "Entry: green wall and console"),
 ("143810", 3.0, 5.0, "Hallway reveal to the stairs"),
 ("152424", 2.0, 4.5, "Living room pan"),
 ("144312", 1.0, 3.0, "Linear fireplace"),
 ("144038", 3.0, 5.5, "Kitchen waterfall island"),
 ("152412", 4.5, 6.5, "Kitchen and dining wide"),
 ("144336", 0.0, 2.0, "Office"),
 ("144428", 1.0, 3.0, "Staircase"),
 ("144836", 1.0, 3.0, "Bedroom seating"),
 ("144908", 0.0, 2.0, "Balcony view"),
 ("144510", 0.0, 2.5, "Primary bath tub"),
 ("144538", 7.0, 9.0, "Walk-in closet"),
 ("144638", 0.0, 2.0, "Arched vanity"),
 ("152402", 0.5, 4.5, "Finale: wide living and kitchen"),
]
segs = []
for k, a, b, t in plan:
    bins = [x for x in A[files[k]]["bins"] if a <= x["t"] < b]
    ti = [x["tilt"] for x in bins if x["tilt"] is not None]
    segs.append({"file": files[k], "start": a, "end": b, "text": t,
                 "measured_tilt": round(statistics.median(ti), 1) if ti else None,
                 "tilt_range": [min(ti), max(ti)] if ti else None})
json.dump({"segments": segs}, open("transcript/cuts.json", "w"), indent=1)
for n, s in enumerate(segs, 1):
    print(n, s["file"][22:28], s["start"], s["end"], s["measured_tilt"], s["tilt_range"], s["text"])
print("total", sum(s["end"] - s["start"] for s in segs))

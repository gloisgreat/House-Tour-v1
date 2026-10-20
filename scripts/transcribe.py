import json, sys
import whisperx

wav, out = sys.argv[1], sys.argv[2]
try:
    import torch
    device, compute = ("cuda", "float16") if torch.cuda.is_available() else ("cpu", "int8")
except Exception:
    device, compute = "cpu", "int8"

def run(device, compute):
    audio = whisperx.load_audio(wav)
    model = whisperx.load_model("large-v3", device, compute_type=compute)
    result = model.transcribe(audio, batch_size=16 if device == "cuda" else 4)
    align_model, meta = whisperx.load_align_model(language_code=result["language"], device=device)
    return whisperx.align(result["segments"], align_model, meta, audio, device), result["language"]

try:
    aligned, lang = run(device, compute)
except Exception as e:
    if device != "cuda":
        raise
    print(f"CUDA failed ({e}); falling back to CPU int8", file=sys.stderr)
    aligned, lang = run("cpu", "int8")

words = [w for s in aligned["segments"] for w in s.get("words", [])]
json.dump({"language": lang, "segments": aligned["segments"], "words": words}, open(out, "w"), indent=1)
print(f"wrote {out}: {len(words)} words")

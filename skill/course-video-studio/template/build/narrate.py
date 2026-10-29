# -*- coding: utf-8 -*-
"""Narrate course videos: Gemini TTS per block, verified by a Hebrew Whisper pass, word-timed.

    python -X utf8 narrate.py m1l1 m1l2 ...     (or "all")

Per block (cached by text hash in videos/<id>/build/audio/):
  1. TTS (Gemini, voice in VOICE). The WAV container is unwrapped to its data chunk (clicks otherwise).
  2. Trim edges, apply TEMPO, transcribe with word timestamps.
  3. Check consonant similarity + word count against the script; retake up to MAX_TAKES.
  4. Align script words to heard words -> times relative to the block.
Then: lead silence + blocks + gaps + tail -> clip/assets/audio/lesson.m4a, build/words.json (segments).
Markup in block text: {display|spoken} shows `display` in captions and sends `spoken` to TTS.
"""
import base64
import difflib
import os
import hashlib
import json
import re
import struct
import subprocess
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from course import BUILD, ROOT, VIDEOS, load_lesson, lesson_ids

# GOOGLE_API_KEY comes from the environment, or from a .env file (GOOGLE_ENV_FILE, the course folder, or build/).
ENV_FILES = [Path(p) for p in (os.environ.get("GOOGLE_ENV_FILE"), ROOT / ".env", BUILD / ".env") if p]
TTS_MODEL = "gemini-3.8-flash-tts"
VOICE = "Charon"
STYLE = ""
SAMPLE_RATE = 24000
TEMPO = 1.0
LEAD, GAP, TAIL = 1.4, 0.5, 4.0
SR = 48000
MAX_TAKES = 4
MIN_RATIO = 0.80
WORD_RANGE = (0.85, 1.18)
WHISPER = "ivrit-ai/whisper-large-v3-turbo-ct2"
TTS_WORKERS = 3
EDGE_DB = "-45dB"
FADE = 0.012
TRIM = (f"silenceremove=start_periods=1:start_threshold={EDGE_DB}:start_silence=0.05,afade=t=in:d={FADE},"
        f"areverse,silenceremove=start_periods=1:start_threshold={EDGE_DB}:start_silence=0.12,afade=t=in:d={FADE},"
        f"areverse,atempo={TEMPO},aresample={SR},aformat=sample_fmts=s16:channel_layouts=mono")
MARKUP = re.compile(r"\{([^|{}]+)\|([^|{}]+)\}")
NIQQUD = re.compile("[\u0591-\u05c7]")
NON_HEB = re.compile("[^\u05d0-\u05ea ]")
MATRES = re.compile("[וי]")
SENT_END = re.compile(r"[.?!:]$")
TRANSLIT = {
    "claude": "קלוד", "code": "קוד", "opus": "אופוס", "sonnet": "סונט", "haiku": "הייקו", "windows": "ווינדוס",
    "mac": "מק", "pro": "פרו", "max": "מקס", "manual": "מנואל", "auto": "אוטו", "plan": "פלאן", "word": "וורד",
    "excel": "אקסל", "chatgpt": "צטגיפיטי", "google": "גוגל", "gmail": "גימייל", "youtube": "יוטיוב",
    "whatsapp": "ווטסאפ", "pdf": "פידיאף", "ai": "איאי", "skills": "סקילס", "skill": "סקיל", "new": "ניו",
    "accept": "אקספט", "edits": "אדיטס", "bypass": "ביפאס", "permissions": "פרמישנס", "download": "דאונלוד",
    "folder": "פולדר", "open": "אופן", "allow": "אלאו", "deny": "דיני", "chat": "צט", "settings": "סטינגס",
    "privacy": "פרייבסי", "connectors": "קונקטורס", "scheduled": "סקדולד", "this": "דיס", "computer": "קומפיוטר",
    "md": "אמדי", "claudemd": "קלודאמדי", "rewind": "ריוויינד", "usage": "יוסג", "model": "מודל",
    "improvement": "אימפרובמנט", "drive": "דרייב", "calendar": "קלנדר", "routine": "רוטין", "routines": "רוטינס",
}


# ---------- text ----------
def units(block):
    """[(display_words, spoken_words)] for one block."""
    out, pos = [], 0
    for m in MARKUP.finditer(block):
        out += [([w], [w]) for w in block[pos:m.start()].split()]
        out.append((m.group(1).split(), m.group(2).split()))
        pos = m.end()
    out += [([w], [w]) for w in block[pos:].split()]
    return [u for u in out if u[0]]


def spoken_text(block):
    return MARKUP.sub(lambda m: m.group(2), block)


def key(word):
    w = NIQQUD.sub("", word).lower()
    latin = re.sub(r"[^a-z]", "", w)
    if latin and latin in TRANSLIT:
        w = TRANSLIT[latin]
    w = NON_HEB.sub("", w.replace("-", ""))
    return MATRES.sub("", w)


def score(expected_words, heard_words):
    e = " ".join(k for k in map(key, expected_words) if k)
    h = " ".join(k for k in map(key, heard_words) if k)
    return difflib.SequenceMatcher(None, e, h, autojunk=False).ratio(), len(h.split()) / max(1, len(e.split()))


# ---------- audio ----------
def load_key():
    if os.environ.get("GOOGLE_API_KEY"):
        return os.environ["GOOGLE_API_KEY"].strip()
    for env in ENV_FILES:
        if env.exists():
            for line in env.read_text(encoding="utf-8").splitlines():
                if line.startswith("GOOGLE_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"')
    raise SystemExit("GOOGLE_API_KEY not found. Set it in the environment, or put a line GOOGLE_API_KEY=... in a .env "
                     "file in the course folder. Get a key at https://aistudio.google.com/apikey")


def run(args):
    r = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode:
        raise SystemExit(f"{args[0]} failed: {r.stderr[-600:]}")


def duration(path):
    return float(subprocess.run(["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                                capture_output=True, text=True).stdout)


def extract_pcm(blob):
    if blob[:4] != b"RIFF":
        return blob
    i = 12
    while i + 8 <= len(blob):
        cid, size = blob[i:i + 4], struct.unpack("<I", blob[i + 4:i + 8])[0]
        if cid == b"data":
            return blob[i + 8:i + 8 + size]
        i += 8 + size + (size & 1)
    raise SystemExit("TTS returned a WAV without a data chunk")


def write_wav(pcm, path):
    with open(path, "wb") as f:
        f.write(b"RIFF" + struct.pack("<I", 36 + len(pcm)) + b"WAVE")
        f.write(b"fmt " + struct.pack("<IHHIIHH", 16, 1, 1, SAMPLE_RATE, SAMPLE_RATE * 2, 2, 16))
        f.write(b"data" + struct.pack("<I", len(pcm)) + pcm)


def synthesize(api_key, text, out):
    body = {"contents": [{"parts": [{"text": STYLE + text}]}],
            "generationConfig": {"responseModalities": ["AUDIO"], "speechConfig": {
                "voiceConfig": {"prebuiltVoiceConfig": {"voiceName": VOICE}}}}}
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{TTS_MODEL}:generateContent?key={api_key}"
    for attempt in range(6):
        req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                resp = json.load(r)
            data = resp["candidates"][0]["content"]["parts"][0]["inlineData"]["data"]
            write_wav(extract_pcm(base64.b64decode(data)), out)
            return
        except urllib.error.HTTPError as e:
            msg = e.read().decode(errors="replace")[:200]
            print(f"  TTS HTTP {e.code}: {msg}", flush=True)
            if e.code not in (429, 500, 503):
                raise
        except (KeyError, IndexError, urllib.error.URLError, TimeoutError) as e:
            print(f"  TTS error {e!r}", flush=True)
        time.sleep(20 * (attempt + 1))
    raise SystemExit("TTS failed: retries exhausted")


# ---------- alignment ----------
def align(script_keys, heard):
    hk = [key(h["w"]) for h in heard]
    sm = difflib.SequenceMatcher(None, script_keys, hk, autojunk=False)
    t = [None] * len(script_keys)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal" or (tag == "replace" and i2 - i1 == j2 - j1):
            for d in range(i2 - i1):
                t[i1 + d] = (heard[j1 + d]["s"], heard[j1 + d]["e"])
        elif tag == "replace" and j2 > j1:
            s, e = heard[j1]["s"], heard[j2 - 1]["e"]
            step = (e - s) / (i2 - i1)
            for d in range(i2 - i1):
                t[i1 + d] = (s + d * step, s + (d + 1) * step)
    missing = sum(x is None for x in t)
    i = 0
    while i < len(t):
        if t[i] is not None:
            i += 1
            continue
        j = i
        while j < len(t) and t[j] is None:
            j += 1
        s = t[i - 1][1] if i else 0.0
        e = t[j][0] if j < len(t) else s + 0.35 * (j - i)
        step = (e - s) / (j - i)
        for k in range(i, j):
            t[k] = (s + (k - i) * step, s + (k - i + 1) * step)
        i = j
    return t, missing


def display_times(us, spoken_times):
    """Spread each unit's spoken time range over its display words."""
    out, k = [], 0
    for disp, spk in us:
        s, e = spoken_times[k][0], spoken_times[k + len(spk) - 1][1]
        k += len(spk)
        step = (e - s) / len(disp)
        out += [(w, s + n * step, s + (n + 1) * step) for n, w in enumerate(disp)]
    return out


# ---------- per block ----------
def raw_hash(block):
    return hashlib.sha1((VOICE + TTS_MODEL + block).encode()).hexdigest()[:12]


class Narrator:
    def __init__(self):
        from faster_whisper import WhisperModel
        self.model = WhisperModel(WHISPER, device="cpu", compute_type="int8", cpu_threads=12)
        self.api_key = load_key()

    def hear(self, wav):
        segs, _ = self.model.transcribe(str(wav), language="he", word_timestamps=True,
                                        condition_on_previous_text=False, beam_size=5)
        return [{"w": w.word.strip(), "s": w.start, "e": w.end} for s in segs for w in s.words if w.word.strip()]

    def check(self, raw, fin, block):
        run(["ffmpeg", "-y", "-v", "error", "-i", str(raw), "-af", TRIM, "-c:a", "pcm_s16le", str(fin)])
        heard = self.hear(fin)
        us = units(block)
        spk = [w for _, s in us for w in s]
        ratio, wc = score(spk, [h["w"] for h in heard])
        return ratio, wc, heard, us, spk

    def block(self, adir, block, pre=None):
        h = raw_hash(block)
        meta = adir / f"b_{h}_t{TEMPO}.json"
        if meta.exists():
            return json.loads(meta.read_text(encoding="utf-8"))
        raw, fin = adir / f"b_{h}_raw.wav", adir / f"b_{h}.wav"
        best = None
        for take in range(MAX_TAKES):
            if not (take == 0 and raw.exists()):
                synthesize(self.api_key, spoken_text(block), raw)
            ratio, wc, heard, us, spk = self.check(raw, fin, block)
            ok = ratio >= MIN_RATIO and WORD_RANGE[0] <= wc <= WORD_RANGE[1]
            print(f"    take {take + 1}: ratio={ratio:.2f} words={wc:.2f} {'OK' if ok else 'RETAKE'}", flush=True)
            if best is None or ratio > best[0]:
                best = (ratio, wc)
                (adir / f"b_{h}_best.wav").write_bytes(fin.read_bytes())
                best_data = (heard, us, spk)
            if ok:
                break
        else:
            print(f"    !! block kept with best ratio {best[0]:.2f} - listen to it", flush=True)
            fin.write_bytes((adir / f"b_{h}_best.wav").read_bytes())
            heard, us, spk = best_data
        times, missing = align([key(w) for w in spk], heard)
        words = display_times(us, times)
        res = {"wav": fin.name, "dur": duration(fin), "ratio": round(best[0], 3), "missing": missing,
               "words": [[w, round(s, 3), round(e, 3)] for w, s, e in words]}
        meta.write_text(json.dumps(res, ensure_ascii=False), encoding="utf-8")
        return res


def segments(words):
    segs, cur = [], []
    for w in words:
        cur.append(w)
        if SENT_END.search(w["w"]) and len(cur) >= 3:
            segs.append(cur)
            cur = []
    if cur:
        segs.append(cur)
    return [{"s": c[0]["s"], "e": c[-1]["e"], "text": " ".join(x["w"] for x in c), "words": c} for c in segs]


def assemble(vid, results):
    adir = vid / "build" / "audio"
    out_dir = vid / "clip" / "assets" / "audio"
    out_dir.mkdir(parents=True, exist_ok=True)
    gap = adir / "gap.wav"
    lead, tail = adir / "lead.wav", adir / "tail.wav"
    for p, d in ((gap, GAP), (lead, LEAD), (tail, TAIL)):
        run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"anullsrc=r={SR}:cl=mono", "-t", str(d), "-c:a", "pcm_s16le", str(p)])
    parts, words, t = [lead], [], LEAD
    for k, r in enumerate(results):
        parts.append(adir / r["wav"])
        words += [{"w": w, "s": round(t + s, 3), "e": round(t + e, 3)} for w, s, e in r["words"]]
        t += r["dur"]
        if k < len(results) - 1:
            parts.append(gap)
            t += GAP
    parts.append(tail)
    lst = adir / "concat.txt"
    lst.write_text("".join(f"file '{p.as_posix()}'\n" for p in parts), encoding="utf-8")
    joined = adir / "joined.wav"
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c:a", "pcm_s16le", str(joined)])
    run(["ffmpeg", "-y", "-v", "error", "-i", str(joined), "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-ar", str(SR),
         "-c:a", "aac", "-b:a", "160k", str(out_dir / "lesson.m4a")])
    (vid / "build" / "words.json").write_text(json.dumps(segments(words), ensure_ascii=False, indent=0), encoding="utf-8")
    return duration(out_dir / "lesson.m4a"), len(words)


def narrate(nar, lid):
    vid = VIDEOS / lid
    blocks = load_lesson(lid).BLOCKS
    adir = vid / "build" / "audio"
    adir.mkdir(parents=True, exist_ok=True)
    print(f"== {lid}: {len(blocks)} blocks", flush=True)
    with ThreadPoolExecutor(TTS_WORKERS) as ex:   # prefetch first takes in parallel
        def pre(b):
            raw = adir / f"b_{raw_hash(b)}_raw.wav"
            if not raw.exists():
                synthesize(nar.api_key, spoken_text(b), raw)
        list(ex.map(pre, blocks))
    results = []
    for k, b in enumerate(blocks):
        print(f"  block {k + 1}/{len(blocks)}", flush=True)
        results.append(nar.block(adir, b))
    dur, n = assemble(vid, results)
    worst = min(r["ratio"] for r in results)
    print(f"== {lid}: {dur:.1f}s, {n} words, worst block ratio {worst:.2f}", flush=True)


def main():
    ids = lesson_ids(sys.argv[1:])
    nar = Narrator()
    for lid in ids:
        narrate(nar, lid)
    print("NARRATION DONE")


if __name__ == "__main__":
    main()

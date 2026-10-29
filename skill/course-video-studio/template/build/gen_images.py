# -*- coding: utf-8 -*-
"""Course illustrations with Gemini (cheapest image model; verify price on the day).

    python -X utf8 gen_images.py [names...]      -> common/img/<name>.png (1920x1080), skips existing
    python -X utf8 gen_images.py --edit <name> "Change ONLY ..."   (keeps the original as <name>_v1.png)
    python -X utf8 gen_images.py --sheet          -> qc_images.jpg contact sheet
"""
import base64
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

from course import BUILD, COMMON
from narrate import load_key

MODEL = os.environ.get("IMG_MODEL", "gemini-3.1-flash-lite-image")
EDIT_MODEL = "gemini-3.1-flash-image"
OUT = COMMON / "img"
STYLE = (" ART STYLE: modern flat 2D vector editorial illustration, clean rounded shapes, soft gradients, gentle grain, "
         "palette of deep navy blue and charcoal with warm coral-orange and cream highlights, calm cozy evening light, "
         "wide 16:9 composition that fills the whole frame edge to edge. ")
PEOPLE = (" PEOPLE RULES (STRICT): modest modern Israeli people. Men wear long or short sleeved shirts, some wear a knitted "
          "kippah. Any girl has bare uncovered hair. A married woman wears only a tichel: a scarf over the hair, tied in a knot "
          "at the back of the head, face, chin, jawline and neck fully visible; NOT a hijab, NOT wrapped around the face, chin "
          "or neck, NOT pinned under the chin, nothing Arab or Muslim style. No hijab, no veil, no hood on anyone. ")
TAIL = " No text, no letters, no numbers, no captions, no logos, no watermark, no robots."

# One entry per illustration: name -> what is in the picture. STYLE, PEOPLE and TAIL are appended automatically.
# Write 'No people.' at the end of a scene without people. Add your own scenes and run: python -X utf8 gen_images.py <name>
SCENES = {
    "helper-desk": "A friendly middle-aged man with a knitted kippah sits at a home desk with an open laptop; from the laptop "
                   "a small glowing coral spark of light sorts floating paper documents into neat folders in the air.",
    "blueprint": "An architect's blueprint spread on a wooden table with a pencil, a ruler and a small model house. No people.",
    "road-sunrise": "A winding road through green hills toward a sunrise, with small milestone posts along the road. No people.",
    "magnifier": "A magnifying glass over a stack of open books and printed pages; small green check marks and one red "
                 "question mark float above the pages. No people.",
}


def post(url, payload):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            print("  HTTP", e.code, e.read().decode("utf-8", "ignore")[:200], flush=True)
            if e.code not in (429, 500, 503):
                raise
        time.sleep(15 * (attempt + 1))
    raise SystemExit("image API retries exhausted")


def png_of(resp):
    for c in resp.get("candidates", []):
        for p in c.get("content", {}).get("parts", []):
            d = p.get("inlineData") or p.get("inline_data")
            if d and d.get("data"):
                return base64.b64decode(d["data"])
    return None


def save(raw, out):
    tmp = out.with_suffix(".raw")
    tmp.write_bytes(raw)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(tmp), "-vf",
                    "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,setsar=1", str(out)], check=True)
    tmp.unlink()


def one(key, name):
    out = OUT / f"{name}.png"
    if out.exists():
        return f"skip {name}"
    subj = SCENES[name]
    prompt = subj + STYLE + (PEOPLE if "No people" not in subj else "") + TAIL
    resp = post(f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={key}",
                {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"imageConfig": {"aspectRatio": "16:9"}}})
    raw = png_of(resp)
    if not raw:
        return f"NO IMAGE {name}: {json.dumps(resp)[:200]}"
    save(raw, out)
    return f"saved {name}"


def edit(key, name, instruction):
    src = OUT / f"{name}.png"
    backup = OUT / f"{name}_v1.png"
    if not backup.exists():
        backup.write_bytes(src.read_bytes())
    data = base64.b64encode(src.read_bytes()).decode()
    resp = post(f"https://generativelanguage.googleapis.com/v1beta/models/{EDIT_MODEL}:generateContent?key={key}",
                {"contents": [{"parts": [{"inlineData": {"mimeType": "image/png", "data": data}},
                                         {"text": instruction + " Keep EVERYTHING else exactly the same."}]}],
                 "generationConfig": {"imageConfig": {"aspectRatio": "16:9"}}})
    raw = png_of(resp)
    if not raw:
        raise SystemExit(f"edit returned no image: {json.dumps(resp)[:300]}")
    save(raw, src)
    print("edited", name)


def sheet():
    from PIL import Image, ImageDraw, ImageFont
    fs = sorted(p for p in OUT.glob("*.png") if not p.stem.endswith("_v1"))
    W, H, cols = 480, 270, 4
    rows = (len(fs) + cols - 1) // cols
    sh = Image.new("RGB", (cols * W, rows * (H + 26)), "white")
    try:
        font = ImageFont.truetype("arial.ttf", 18)
    except OSError:   # no Arial outside Windows
        font = ImageFont.load_default()
    d = ImageDraw.Draw(sh)
    for k, f in enumerate(fs):
        im = Image.open(f).convert("RGB").resize((W - 6, H - 6))
        x, y = (k % cols) * W, (k // cols) * (H + 26)
        sh.paste(im, (x + 3, y + 3))
        d.text((x + 6, y + H + 2), f.stem, fill="black", font=font)
    sh.save(BUILD / "qc_images.jpg", quality=82)
    print("sheet", len(fs))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    args = sys.argv[1:]
    if args[:1] == ["--sheet"]:
        return sheet()
    key = load_key()
    if args[:1] == ["--edit"]:
        return edit(key, args[1], args[2])
    names = args or list(SCENES)
    with ThreadPoolExecutor(4) as ex:
        for msg in ex.map(lambda n: one(key, n), names):
            print(msg, flush=True)
    sheet()


if __name__ == "__main__":
    main()

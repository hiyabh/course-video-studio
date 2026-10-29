# -*- coding: utf-8 -*-
"""Build one or more lesson videos' HyperFrames projects from videos/<id>/lesson.py + words.json.

    python -X utf8 build_video.py m1l1 [m1l2 ...|all] [--lint]

Steps per lesson: video.json + chapter_spec.json + beats/*.json -> copy template and media ->
clean_words -> make_chapters -> make_index (silent) -> beats -> density_check (warning only).
"""
import json
import os
import shutil
import subprocess
import sys

from course import COMMON, COURSE, ENGINE, PARTS, VIDEOS, BUILD, lesson_ids, lesson_meta, load_lesson

TEMPLATE = BUILD / "clip_template"
HF = "hyperframes@0.8.106"
IMG_BEATS = ("story", "imgtext", "split")


LIST_KEYS = ("nodes", "items", "steps_txt", "words")


def normalize(beat):
    """Diagram/list items written as {"label": ..} dicts become plain strings."""
    for k in LIST_KEYS:
        if isinstance(beat.get(k), list):
            beat[k] = [x.get("label") or x.get("h") or x.get("text") if isinstance(x, dict) else x for x in beat[k]]
    return beat


def eyebrow(meta):
    m = meta["module"]
    if m["part"] == "בונוס":
        return f'בונוס · {m["name"]}'
    if len(PARTS) == 1:
        return f'פרק {m["n"]} · {m["name"]}'
    return f'{meta["part_name"]} · פרק {m["n"]} · {m["name"]}'


def sync_title(beat, meta):
    """The lesson title card always follows course.py, so reordering lessons never needs a lesson.py edit."""
    beat.update(badge=f'שיעור {meta["num"]}', title=meta["title"], sub=meta["promise"], eyebrow=eyebrow(meta))


def write_config(lid, les, meta):
    b = VIDEOS / lid / "build"
    (b / "beats").mkdir(parents=True, exist_ok=True)
    for old in (b / "beats").glob("*.json"):
        old.unlink()
    video = {"title": meta["title"], "subtitle": meta["promise"], "density_max_gap": 12, "keywords": getattr(les, "KEYWORDS", []),
             "brand": f'{COURSE["brand"]} · שיעור {meta["num"]}', "fixes": {}, "blocked_names": [], "blocked_stems": [],
             "timed_drops": []}
    (b / "video.json").write_text(json.dumps(video, ensure_ascii=False, indent=1), encoding="utf-8")
    spec = [{"id": c["id"], "title": c["title"], "ink": c.get("ink", "torah"), "at": c.get("at", 0)} for c in les.CHAPTERS]
    (b / "chapter_spec.json").write_text(json.dumps(spec, ensure_ascii=False, indent=1), encoding="utf-8")
    sync_title(les.CHAPTERS[0]["beats"][0], meta)
    for c in les.CHAPTERS:
        (b / "beats" / f'{c["id"]}.json').write_text(json.dumps(
            {"ghost": c.get("ghost", ""), "keywords": c.get("keywords", []), "beats": [normalize(b) for b in c["beats"]]}, ensure_ascii=False, indent=1),
            encoding="utf-8")


def copy_media(lid, les):
    clip = VIDEOS / lid / "clip"
    for sub in ("assets/img", "assets/shots", "compositions"):
        (clip / sub).mkdir(parents=True, exist_ok=True)
    for item in TEMPLATE.rglob("*"):
        if item.is_file():
            dst = clip / item.relative_to(TEMPLATE)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, dst)
    missing = []
    for c in les.CHAPTERS:
        for bt in c["beats"]:
            if bt["t"] in IMG_BEATS:
                src, dst = COMMON / "img" / f'{bt["img"]}.png', clip / "assets" / "img" / f'{bt["img"]}.png'
            elif bt["t"] == "shot":
                src, dst = COMMON / "shots" / bt["img"], clip / "assets" / "shots" / bt["img"]
            else:
                continue
            if src.exists():
                shutil.copy2(src, dst)
            else:
                missing.append(src.name)
    return missing


def run_engine(lid, script, *args, check=True):
    env = {**os.environ, "VID": str(VIDEOS / lid), "PYTHONIOENCODING": "utf-8"}
    r = subprocess.run([sys.executable, "-X", "utf8", str(ENGINE / script), *args], env=env, cwd=str(ENGINE),
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = (r.stdout + r.stderr).strip()
    if r.returncode and check:
        raise SystemExit(f"{lid}: {script} failed\n{out[-2500:]}")
    return r.returncode, out


def build(lid, lint):
    meta = lesson_meta(lid)
    les = load_lesson(lid)
    if not (VIDEOS / lid / "build" / "words.json").exists():
        raise SystemExit(f"{lid}: no words.json - run narrate.py {lid} first")
    marker = VIDEOS / lid / "build" / "BUILD_OK"
    marker.unlink(missing_ok=True)
    write_config(lid, les, meta)
    missing = copy_media(lid, les)
    if missing:
        raise SystemExit(f"{lid}: missing media {missing}")
    for script, args in (("clean_words.py", ()), ("make_chapters.py", ()), ("make_index.py", ("--no-audio",))):
        run_engine(lid, script, *args)
    code, out = run_engine(lid, "beats.py", check=False)
    print(f"[{lid}] " + out.replace("\n", f"\n[{lid}] "))
    if code:
        return False
    code, out = run_engine(lid, "density_check.py", check=False)
    print(f"[{lid}] " + out.splitlines()[0] + ("" if code == 0 else "\n" + out))
    if lint:
        r = subprocess.run(f"npx --yes {HF} lint", cwd=str(VIDEOS / lid / "clip"), shell=True, capture_output=True,
                           text=True, encoding="utf-8", errors="replace")
        print(f"[{lid}] lint: " + (r.stdout + r.stderr).strip().splitlines()[-1])
    marker.write_text("ok", encoding="utf-8")
    return True


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    ok = [build(lid, "--lint" in sys.argv) for lid in lesson_ids(args)]
    print("BUILD OK" if all(ok) else "BUILD HAD ERRORS")


if __name__ == "__main__":
    main()

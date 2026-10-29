# -*- coding: utf-8 -*-
"""Start a new course project from the template.

    python -X utf8 new_course.py "<course folder>" ["<course title>"]

Creates <course folder>/build (engine, pipeline, demo lesson), .env.example and .gitignore.
Refuses to touch a folder that already has a build/ inside.
"""
import shutil
import sys
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parent.parent / "template"
GITIGNORE = """.env
__pycache__/
build/videos/*/build/
build/videos/*/clip/
build/qc/
build/qc_images.jpg
סרטונים/
"""
ENV_EXAMPLE = "# Gemini key for narration and illustrations: https://aistudio.google.com/apikey\nGOOGLE_API_KEY=\n"


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    root = Path(sys.argv[1]).expanduser().resolve()
    if (root / "build").exists():
        raise SystemExit(f"{root / 'build'} already exists - not overwritten")
    root.mkdir(parents=True, exist_ok=True)
    shutil.copytree(TEMPLATE / "build", root / "build", ignore=shutil.ignore_patterns("__pycache__"))
    (root / "build" / "common" / "shots").mkdir(parents=True, exist_ok=True)
    for name, text in ((".gitignore", GITIGNORE), (".env.example", ENV_EXAMPLE)):
        if not (root / name).exists():
            (root / name).write_text(text, encoding="utf-8")
    if len(sys.argv) > 2:
        course = root / "build" / "course.py"
        course.write_text(course.read_text(encoding="utf-8").replace("שם הקורס", sys.argv[2]), encoding="utf-8")
    print(f"course created: {root}")
    print("next: edit build/course.py, put GOOGLE_API_KEY in .env, then run check_lesson.py demo1 from build/")


if __name__ == "__main__":
    main()

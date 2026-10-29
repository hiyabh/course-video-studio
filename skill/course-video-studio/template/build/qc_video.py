# -*- coding: utf-8 -*-
"""Contact sheet of a delivered lesson: one frame every STEP seconds -> qc/video_<id>.jpg

    python -X utf8 qc_video.py m4l1 [...]
"""
import subprocess
import sys

from course import BUILD, lesson_ids
from render_video import out_paths

STEP = 7


def main():
    (BUILD / "qc").mkdir(exist_ok=True)
    for lid in lesson_ids(sys.argv[1:]):
        mp4 = out_paths(lid)[0]
        if not mp4.exists():
            print(lid, "not delivered")
            continue
        out = BUILD / "qc" / f"video_{lid}.jpg"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(mp4), "-vf",
                        f"fps=1/{STEP},scale=480:270,drawtext=text='%{{pts\:hms}}':x=8:y=8:fontsize=20:fontcolor=yellow:box=1:boxcolor=black,tile=5x5",
                        "-frames:v", "1", "-q:v", "4", str(out)], check=True)
        print(out.name)


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""Draw every SHOT mark of the given lessons onto its screenshot -> qc/marks_<lesson>_<k>.jpg for review.

    python -X utf8 qc_marks.py m4l6 m4l8 [...|all]
"""
import sys

from PIL import Image, ImageDraw, ImageFont

from course import BUILD, COMMON, lesson_ids, load_lesson

QC = BUILD / "qc"
MAX_W = 1100


def main():
    QC.mkdir(exist_ok=True)
    font = ImageFont.truetype("arial.ttf", 26)
    for lid in lesson_ids(sys.argv[1:]):
        k = 0
        for c in load_lesson(lid).CHAPTERS:
            for b in c["beats"]:
                if b["t"] != "shot" or not b.get("marks"):
                    continue
                im = Image.open(COMMON / "shots" / b["img"]).convert("RGB")
                w, h = im.size
                d = ImageDraw.Draw(im)
                for n, m in enumerate(b["marks"]):
                    x, y, bw, bh = m["box"]
                    box = (x * w / 100, y * h / 100, (x + bw) * w / 100, (y + bh) * h / 100)
                    d.rectangle(box, outline=(255, 60, 0), width=6)
                    d.text((box[0] + 6, box[1] + 4), str(n + 1), fill=(255, 0, 0), font=font)
                im.thumbnail((MAX_W, MAX_W))
                out = QC / f"marks_{lid}_{k}_{b['img'].split('.')[0]}.jpg"
                im.save(out, quality=80)
                print(out.name, [m.get("label", "") for m in b["marks"]])
                k += 1


if __name__ == "__main__":
    main()

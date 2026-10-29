# -*- coding: utf-8 -*-
"""Course beats: app (animated Claude Code desktop mock), shot (real screenshot + marks), files
(messy files fly into folders), prompt (typed "try it" card), steps (numbered cards).
Every renderer returns (html, js_lines); times are chapter-local seconds."""
import json
import math
from pathlib import Path

import sfx
from beat_util import GOLDEN, breathe, esc, q, times

# ---- app mock geometry (px inside the 1920x1080 frame) ----
APP_W, APP_H, APP_X, APP_Y = 1540, 690, 190, 140
CHAT_H = 470
LINE_H = 44
SAY_CHARS, BUB_CHARS = 66, 50
STEP_GAP = 18
HEIGHTS = {"tool": 52, "done": 54, "file": 84, "ask": 214}
TYPE_RATE, TYPE_MIN, TYPE_MAX = 0.035, 0.8, 2.6
SIDE_ITEMS = [("＋", "New"), ("◇", "Artifacts"), ("◷", "Scheduled"), ("▣", "Customize"), ("⋯", "More")]
BURST_N, BURST_R = 12, 70
BURST_COLORS = ("#EE9A70", "#86B9EA", "#6CCB9C", "#E9C440", "#B9A2E8", "#F28DB2")
HI_TARGETS = ("input", "plus", "env", "folder", "mode", "model", "code", "scheduled", "customize")


def _lines(text, per):
    return max(1, math.ceil(len(text) / per))


def _height(st):
    k = st["k"]
    if k == "you":
        return 30 + _lines(st["text"], BUB_CHARS) * LINE_H
    if k == "say":
        return 14 + _lines(st["text"], SAY_CHARS) * LINE_H
    return HEIGHTS[k]


def _step_html(i, st):
    k, text = st["k"], esc(st.get("text", ""))
    if k == "you":
        return f'<div class="m you" data-i="{i}"><div class="bub">{text}</div></div>'
    if k == "say":
        return f'<div class="m say" data-i="{i}"><i class="spark"></i><div class="tx">{text}</div></div>'
    if k == "tool":
        return (f'<div class="m tool" data-i="{i}"><i class="spin"></i><i class="tick">✓</i>'
                f'<b class="tn">{esc(st.get("tool", "Read"))}</b><span class="td">{text}</span></div>')
    if k == "done":
        burst = "".join(f'<i style="background:{BURST_COLORS[j % len(BURST_COLORS)]}"></i>' for j in range(BURST_N))
        return f'<div class="m done" data-i="{i}"><i class="ok">✓<b class="burst">{burst}</b></i><span>{text}</span></div>'
    if k == "file":
        return (f'<div class="m file" data-i="{i}"><div class="fc"><i class="fi">{esc(st.get("icon", "📄"))}</i>'
                f'<div><div class="fn">{text}</div><div class="ft">{esc(st.get("sub", ""))}</div></div></div></div>')
    if k == "ask":
        return (f'<div class="m ask" data-i="{i}"><div class="ah">{text}</div>'
                f'<div class="ad">{esc(st.get("detail", ""))}</div>'
                f'<div class="btns"><span class="b allow">{esc(st.get("yes", "Allow"))}</span>'
                f'<span class="b deny">{esc(st.get("no", "Deny"))}</span></div>'
                f'<svg class="cursor" viewBox="0 0 24 24"><path d="M4 2l15 11-7 1-3 7z"/></svg></div>')
    raise SystemExit(f"app step kind {k!r} unknown")


def _chrome(b):
    side = "".join(f'<div class="si si-{n.lower()} hi-{n.lower()}"><i>{ic}</i>{n}</div>' for ic, n in SIDE_ITEMS)
    folder = esc(b.get("folder", "My folder"))
    return (f'<div class="side"><div class="tg"><span>Claude</span><span class="on hi-code">&lt;/&gt; Code</span></div>'
            f'<div class="sr">Search</div>{side}<div class="acct">{esc(b.get("user", "Max"))}</div></div>'
            f'<div class="top">{esc(b.get("session", "New session"))}</div>')


def _bottom(b):
    return (f'<div class="inp hi-input"><i class="plus hi-plus">+</i><span class="ph">Describe a task or ask a question</span>'
            f'{b["_typed"]}<i class="caret"></i><i class="mic">🎙</i></div>'
            f'<div class="stat"><span class="hi-env">🖥 This computer</span><span class="hi-folder">📁 {esc(b.get("folder", "My folder"))}</span>'
            f'<span class="hi-mode">{esc(b.get("mode", "Manual"))}</span><span class="gap"></span>'
            f'<span class="hi-model">{esc(b.get("model", "Opus 5.5"))}</span></div>')


def _type_js(sel, text, t, dur):
    """Seek-safe typewriter on one element (proxy writes a prefix of the text)."""
    return (f'(function () {{ const el = R.querySelector("{sel}"); const T = {json.dumps(text, ensure_ascii=False)}; const p = {{ n: 0 }}; '
            f'const w = () => {{ el.textContent = T.slice(0, Math.round(p.n)); }}; w(); '
            f'tl.fromTo(p, {{ n: 0 }}, {{ n: T.length, duration: {dur}, ease: "none", onUpdate: w }}, {t}); }})();')


def _you_js(bid, i, st, t):
    dur = round(min(TYPE_MAX, max(TYPE_MIN, len(st["text"]) * TYPE_RATE)), 2)
    sent = round(t + dur + 0.35, 2)
    sfx.ev("type", t, dur)
    return [f'tl.fromTo(R.querySelector("#{bid} .ph"), {{ opacity: 1 }}, {{ opacity: 0, duration: 0.15 }}, {t});',
            _type_js(f"#{bid} .typed-{i}", st["text"], t, dur),
            f'tl.to(R.querySelector("#{bid} .typed-{i}"), {{ opacity: 0, duration: 0.2 }}, {sent});',
            f'tl.to(R.querySelector("#{bid} .ph"), {{ opacity: 1, duration: 0.2 }}, {sent + 0.3});',
            f'K.in(tl, R, {q(bid, ".m", i)}, {sent}, {{ y: 40, dur: 0.45 }});'], sent


def _step_js(bid, i, st, t):
    k, el = st["k"], q(bid, ".m", i)
    if k == "you":
        return _you_js(bid, i, st, t)
    if k == "say":
        return [f'K.in(tl, R, {el}, {t}, {{ y: 16 }});'], t
    if k == "tool":
        return [f'K.in(tl, R, {el}, {t}, {{ x: 30, y: 0, dur: 0.35 }});',
                f'tl.fromTo({el}.querySelector(".spin"), {{ rotation: 0, opacity: 1 }}, {{ rotation: 540, duration: 1.1, ease: "none" }}, {t});',
                f'tl.to({el}.querySelector(".spin"), {{ opacity: 0, duration: 0.1 }}, {t + 1.1});',
                f'K.pop(tl, R, [{el}.querySelector(".tick")], {t + 1.1}, {{ overshoot: 3 }});'], t
    if k == "done":
        burst = (f'{el}.querySelectorAll(".burst i").forEach((p, j) => tl.fromTo(p, {{ opacity: 1, x: 0, y: 0, scale: 1 }}, '
                 f'{{ opacity: 0, x: Math.cos(j * {round(6.2832 / BURST_N, 4)}) * {BURST_R}, y: Math.sin(j * {round(6.2832 / BURST_N, 4)}) * {BURST_R}, '
                 f'scale: 0.4, duration: 0.9, ease: "power3.out" }}, {t + 0.25}));')
        sfx.ev("pop", t + 0.2)
        return [f'K.in(tl, R, {el}, {t}, {{ y: 14 }});', f'K.pop(tl, R, [{el}.querySelector(".ok")], {t + 0.15}, {{ overshoot: 3 }});', burst], t
    if k == "file":
        sfx.ev("pop", t)
        return [f'K.pop(tl, R, {el}, {t}, {{ overshoot: 1.6 }});'], t
    click = round(t + st.get("think", 1.6), 2)
    sfx.ev("click", click)
    deny = st.get("click", "yes") == "no"
    btn, color, cx = (".deny", "#E07A5F", -90) if deny else (".allow", "#6CCB9C", 0)
    return [f'K.in(tl, R, {el}, {t}, {{ y: 50, dur: 0.5 }});',
            f'tl.fromTo({el}.querySelector(".cursor"), {{ opacity: 0, x: 260, y: 90 }}, {{ opacity: 1, x: {cx}, y: 0, duration: 0.8, ease: "power2.inOut" }}, {round(click - 0.9, 2)});',
            f'tl.fromTo({el}.querySelector("{btn}"), {{ scale: 1 }}, {{ scale: 0.9, duration: 0.1, yoyo: true, repeat: 1 }}, {click});',
            f'tl.to({el}.querySelector(".cursor"), {{ opacity: 0, duration: 0.3 }}, {click + 0.5});',
            f'tl.to({el}, {{ borderColor: "{color}", duration: 0.3 }}, {click + 0.1});'], click


def _hi_js(bid, hi, t_list):
    out = []
    for h, t in zip(hi, t_list):
        if h["el"] not in HI_TARGETS:
            raise SystemExit(f"app highlight target {h['el']!r} unknown; use one of {HI_TARGETS}")
        el = f'R.querySelector("#{bid} .hi-{h["el"]}")'
        out.append(f'tl.fromTo({el}, {{ boxShadow: "0 0 0 0px rgba(238,154,112,0)" }}, '
                   f'{{ boxShadow: "0 0 0 6px rgba(238,154,112,0.95)", duration: 0.35, ease: "power2.out" }}, {t});')
        out.append(f'tl.to({el}, {{ boxShadow: "0 0 0 0px rgba(238,154,112,0)", duration: 0.4 }}, {round(t + h.get("hold", 3.0), 2)});')
    return out


def app(bid, b, s, dur, rel, i):
    steps = b.get("steps", [])
    hi = b.get("hi", [])
    n = len(steps)
    t_steps = times(rel[:n], n, s + 0.6, 1.4)
    t_hi = times(rel[n:n + len(hi)], len(hi), (t_steps[-1] if t_steps else s) + 0.8, 3.0)
    msgs = "".join(_step_html(k, st) for k, st in enumerate(steps))
    b = {**b, "_typed": "".join(f'<span class="typed typed-{k}" dir="rtl"></span>' for k, st in enumerate(steps) if st["k"] == "you")}
    # Laptop mockup: bezel + base around the window, entering with a 3D tilt.
    h = (f'<div class="in" style="padding:0"><div class="dev" id="{bid}-dev"><div class="lapbez"><i class="cam"></i></div>'
         f'<div class="app" id="{bid}-app">{_chrome(b)}'
         f'<div class="main"><div class="chat"><div class="ci" id="{bid}-ci">{msgs}</div></div>{_bottom(b)}</div>'
         f'</div><div class="lapbase"><i></i></div></div></div>')
    js = [f'tl.fromTo(R.querySelector("#{bid}-dev"), {{ opacity: 0, y: 90, rotationX: 24, scale: 0.92, transformPerspective: 1800 }}, '
          f'{{ opacity: 1, y: 0, rotationX: 0, scale: 1, duration: 0.9, ease: "power3.out" }}, {s});',
          f'tl.fromTo(R.querySelector("#{bid} .caret"), {{ opacity: 1 }}, {{ opacity: 0, duration: 0.5, repeat: {max(1, int(dur / 0.5) - 1)}, yoyo: true, ease: "steps(1)" }}, {s});']
    used = 0
    for k, (st, t) in enumerate(zip(steps, t_steps)):
        lines, shown = _step_js(bid, k, st, t)
        js += lines
        used += _height(st) + STEP_GAP
        if used > CHAT_H:
            js.append(f'tl.to(R.querySelector("#{bid}-ci"), {{ y: {-(used - CHAT_H)}, duration: 0.5, ease: "power2.out" }}, {shown});')
    return h, js + _hi_js(bid, hi, t_hi)


# ---- real screenshot with marks ----
SHOT_BOX = (1560, 640)
SHOT_TOP = 150
BAR_H = 44


def _img_size(path):
    from PIL import Image
    with Image.open(path) as im:
        return im.size


def _fit(w, h, box):
    k = min(box[0] / w, box[1] / h)
    return round(w * k), round(h * k)


def shot(bid, b, s, dur, rel, i):
    from config import CLIP
    src = CLIP / "assets" / "shots" / b["img"]
    w, h = _fit(*_img_size(src), SHOT_BOX)
    x0, y0 = (1920 - w) // 2, SHOT_TOP + BAR_H
    url = f'<span class="url">{esc(b["url"])}</span>' if b.get("url") else f'<span class="url">{esc(b.get("title", ""))}</span>'
    marks = b.get("marks", [])
    boxes = "".join(
        f'<div class="mk" style="left:{m["box"][0]}%;top:{m["box"][1]}%;width:{m["box"][2]}%;height:{m["box"][3]}%">'
        + (f'<span class="ml">{esc(m["label"])}</span>' if m.get("label") else "") + '</div>' for m in marks)
    h_html = (f'<div class="in" style="padding:0"><div class="shotwin" id="{bid}-w" style="left:{x0}px;top:{SHOT_TOP}px;width:{w}px">'
              f'<div class="sbar"><i></i><i></i><i></i>{url}</div>'
              f'<div class="sview" style="width:{w}px;height:{h}px"><div class="cam" id="{bid}-cam">'
              f'<img src="assets/shots/{esc(b["img"])}" alt="" />{boxes}</div></div></div></div>')
    js = [f'tl.fromTo(R.querySelector("#{bid}-w"), {{ opacity: 0, y: 70, rotationX: 10, rotationY: -16, transformPerspective: 1800 }}, '
          f'{{ opacity: 1, y: 0, rotationX: 0, rotationY: 0, duration: 0.9, ease: "power3.out" }}, {s});',
          f'tl.fromTo(R.querySelector("#{bid}-cam"), {{ scale: 1.0 }}, {{ scale: 1.03, duration: {dur}, ease: "none" }}, {s});']
    zoomed = False
    for k, (m, t) in enumerate(zip(marks, times(rel, len(marks), s + 1.2, 2.5))):
        el = q(bid, ".mk", k)
        js += [f'tl.fromTo({el}, {{ opacity: 0, scale: 1.25 }}, {{ opacity: 1, scale: 1, duration: 0.45, ease: "back.out(2)" }}, {t});']
        if k > 0:
            js.append(f'tl.to({q(bid, ".mk", k - 1)}, {{ opacity: 0.0, duration: 0.3 }}, {t});')
        z = m.get("zoom")
        if z:
            cx, cy = (m["box"][0] + m["box"][2] / 2) / 100, (m["box"][1] + m["box"][3] / 2) / 100
            tx = max(-(z - 1) * w / 2, min((z - 1) * w / 2, (0.5 - cx) * w * z))
            ty = max(-(z - 1) * h / 2, min((z - 1) * h / 2, (0.5 - cy) * h * z))
            js.append(f'tl.to(R.querySelector("#{bid}-cam"), {{ scale: {z}, x: {round(tx)}, y: {round(ty)}, duration: 1.1, ease: "power2.inOut" }}, {t - 0.2});')
            zoomed = True
        elif zoomed:
            js.append(f'tl.to(R.querySelector("#{bid}-cam"), {{ scale: 1.0, x: 0, y: 0, duration: 1.0, ease: "power2.inOut" }}, {t - 0.2});')
            zoomed = False
    return h_html, js


# ---- messy files fly into folders ----
FILE_W, FILE_H = 300, 66
FOLDER_W = 260
MESS_TOP, MESS_H = 250, 290
FOLDER_Y = 640


def _mess_positions(n):
    cols = min(5, n)
    rows = math.ceil(n / cols)
    out = []
    for k in range(n):
        r, c = divmod(k, cols)
        jx = ((k * GOLDEN) % 1 - 0.5) * 70
        jy = (((k * 7 * GOLDEN) % 1) - 0.5) * 40
        x = 1920 - 160 - FILE_W - c * ((1920 - 320 - FILE_W) / max(1, cols - 1)) + jx
        y = MESS_TOP + r * (MESS_H / max(1, rows)) + jy
        out.append((round(x), round(y), round(((k * 3 * GOLDEN) % 1 - 0.5) * 14, 1)))
    return out


def files(bid, b, s, dur, rel, i):
    names, folders = b["files"], b["folders"]
    pos = _mess_positions(len(names))
    nf = len(folders)
    span = min(1600, nf * (FOLDER_W + 70))
    fx = [round(960 + span / 2 - (k + 0.5) * span / nf - FOLDER_W / 2) for k in range(nf)]
    owner = {}
    for k, f in enumerate(folders):
        for idx in f["items"]:
            owner[idx] = k
    chips = "".join(f'<div class="fchip" style="left:{x}px;top:{y}px;transform:rotate({r}deg)">'
                    f'<i>{esc(b.get("icon", "📄"))}</i><span>{esc(n)}</span></div>' for (x, y, r), n in zip(pos, names))
    fold = "".join(f'<div class="fold" style="left:{x}px;top:{FOLDER_Y}px"><div class="ftab"></div><div class="fbody">'
                   f'<span class="fcount">{len(f["items"])}</span></div><div class="fname">{esc(f["name"])}</div></div>'
                   for x, f in zip(fx, folders))
    title = f'<h2 class="h3 gold ftitle">{esc(b.get("title", ""))}</h2>' if b.get("title") else ""
    h = f'<div class="in" style="padding:0">{title}{chips}{fold}</div>'
    js = [f'K.in(tl, R, "#{bid} .ftitle", {s + 0.1}, {{ y: 20 }});'] if title else []
    js.append(f'K.pop(tl, R, "#{bid} .fchip", {s + 0.3}, {{ stagger: 0.07, overshoot: 1.5 }});')
    t_sort = rel[0] if rel else round(s + max(2.5, dur * 0.35), 2)
    js.append(f'K.pop(tl, R, "#{bid} .fold", {round(t_sort - 0.5, 2)}, {{ stagger: 0.12 }});')
    order = sorted(owner)
    for n_, idx in enumerate(order):
        k = owner[idx]
        x, y, _ = pos[idx]
        dx = fx[k] + FOLDER_W / 2 - (x + FILE_W / 2)
        dy = FOLDER_Y + 60 - (y + FILE_H / 2)
        t = round(t_sort + 0.3 + n_ * min(0.16, 3.0 / max(1, len(order))), 2)
        js.append(f'tl.to({q(bid, ".fchip", idx)}, {{ x: {round(dx)}, y: {round(dy)}, rotation: 0, scale: 0.35, opacity: 0, '
                  f'duration: 0.7, ease: "power2.in" }}, {t});')
        js.append(f'tl.fromTo({q(bid, ".fold .fbody", k)}, {{ scaleY: 1 }}, {{ scaleY: 0.9, duration: 0.12, yoyo: true, repeat: 1, '
                  f'immediateRender: false }}, {round(t + 0.65, 2)});')
    t_end = round(t_sort + 1.2 + len(order) * min(0.16, 3.0 / max(1, len(order))), 2)
    js.append(f'K.pop(tl, R, "#{bid} .fcount", {t_end}, {{ stagger: 0.1, overshoot: 3 }});')
    return h, js


# ---- typed "try it yourself" prompt card ----
def prompt(bid, b, s, dur, rel, i):
    text = b["text"]
    h = (f'<div class="in center"><div class="pcard" id="{bid}-pc"><div class="ph2"><span class="ptag">{esc(b.get("title", "נסו בעצמכם"))}</span>'
         f'<span class="pcopy">⧉ העתיקו</span></div><div class="ptext" id="{bid}-pt"></div><i class="pcaret"></i></div>'
         f'<div class="body dim sub pnote">{esc(b.get("note", ""))}</div></div>')
    t0 = s + 0.6
    tdur = round(min(5.0, max(1.4, len(text) * 0.03)), 2)
    sfx.ev("type", t0, tdur)
    js = [f'tl.fromTo(R.querySelector("#{bid}-pc"), {{ opacity: 0, y: 50, scale: 0.96 }}, {{ opacity: 1, y: 0, scale: 1, duration: 0.6, ease: "power3.out" }}, {s});',
          f'K.in(tl, R, "#{bid} .ptag", {s + 0.3}, {{ x: 30, y: 0 }});',
          _type_js(f"#{bid}-pt", text, t0, tdur),
          f'tl.fromTo(R.querySelector("#{bid} .pcaret"), {{ opacity: 1 }}, {{ opacity: 0, duration: 0.45, repeat: {max(1, int(dur / 0.45) - 1)}, yoyo: true, ease: "steps(1)" }}, {s});',
          f'K.pop(tl, R, "#{bid} .pcopy", {round(t0 + tdur + 0.3, 2)}, {{ overshoot: 2.5 }});',
          f'K.in(tl, R, "#{bid} .pnote", {rel[0] if rel else round(t0 + tdur + 0.8, 2)}, {{ y: 20 }});']
    return h, js + breathe(bid, ".pcard", t0 + tdur + 1, dur - tdur - 2, 1.01)


# ---- numbered step cards, right to left ----
def steps(bid, b, s, dur, rel, i):
    items = b["steps"]
    cards = "".join(f'<div class="stc"><div class="stn">{k + 1}</div><div class="sti">{esc(it.get("icon", ""))}</div>'
                    f'<div class="sth">{esc(it["h"])}</div><div class="std">{esc(it.get("d", ""))}</div></div>'
                    for k, it in enumerate(items))
    title = f'<h2 class="h2 gold stt">{esc(b["title"])}</h2>' if b.get("title") else ""
    h = f'<div class="in"><div class="stwrap">{title}<div class="strow">{cards}</div></div></div>'
    js = [f'K.in(tl, R, "#{bid} .stt", {s + 0.1}, {{ y: 30 }});'] if title else []
    for k, t in enumerate(times(rel, len(items), s + 0.7, 0.9)):
        js.append(f'K.in(tl, R, {q(bid, ".stc", k)}, {t}, {{ y: 60, dur: 0.6 }});')
        js.append(f'K.pop(tl, R, [{q(bid, ".stn", k)}], {t + 0.15}, {{ overshoot: 2.6 }});')
    return h, js


# ---- link card: title, address and a scannable QR code ----
QR_PX = 360


def _qr_svg(url):
    import io
    import qrcode
    import qrcode.image.svg
    img = qrcode.make(url, image_factory=qrcode.image.svg.SvgPathImage, border=1)
    buf = io.BytesIO()
    img.save(buf)
    svg = buf.getvalue().decode("utf-8")
    return svg[svg.index("<svg"):].replace("<svg ", f'<svg class="qrsvg" width="{QR_PX}" height="{QR_PX}" ', 1)


def link(bid, b, s, dur, rel, i):
    sfx.ev("chime", s + 0.6)
    h = (f'<div class="in center"><div class="lcard" id="{bid}-lc"><div class="lqr">{_qr_svg(b["url"])}</div>'
         f'<div class="ltxt"><div class="lic">{esc(b.get("icon", "🔗"))}</div><div class="lh">{esc(b["title"])}</div>'
         f'<div class="lurl">{esc(b["url"].split("://")[-1])}</div><div class="lsub">{esc(b.get("sub", ""))}</div></div></div></div>')
    js = [f'tl.fromTo(R.querySelector("#{bid}-lc"), {{ opacity: 0, y: 60, rotation: -2 }}, {{ opacity: 1, y: 0, rotation: 0, duration: 0.7, ease: "back.out(1.6)" }}, {s});',
          f'K.pop(tl, R, "#{bid} .lic", {s + 0.35}, {{ overshoot: 3 }});',
          f'K.in(tl, R, "#{bid} .lh", {s + 0.5}, {{ x: 40, y: 0 }});',
          f'tl.fromTo(R.querySelector("#{bid} .lqr"), {{ opacity: 0, scale: 0.6, rotation: 8 }}, {{ opacity: 1, scale: 1, rotation: 0, duration: 0.7, ease: "back.out(2)" }}, {s + 0.6});',
          f'K.in(tl, R, "#{bid} .lurl", {s + 0.9}, {{ y: 20 }});',
          f'K.in(tl, R, "#{bid} .lsub", {rel[0] if rel else s + 1.3}, {{ y: 20 }});']
    return h, js + breathe(bid, ".lqr", s + 1.5, dur - 2, 1.03)


RENDER = {"app": app, "shot": shot, "files": files, "prompt": prompt, "steps": steps, "link": link}

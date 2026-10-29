# -*- coding: utf-8 -*-
"""Device mockups: phone (the Claude mobile app, Code tab, a conversation that runs on the computer).
Every renderer returns (html, js_lines); times are chapter-local seconds."""
import sfx
from beat_util import breathe, esc, q, times

PHONE_W, PHONE_H, PHONE_TOP, PHONE_LEFT = 470, 820, 110, 300
STEP_GAP = 1.4


def _msg(st):
    k, text = st["k"], esc(st.get("text", ""))
    if k == "you":
        return f'<div class="pm pyou"><span>{text}</span></div>'
    if k == "done":
        return f'<div class="pm pdone"><i>✓</i><span>{text}</span></div>'
    if k == "ask":
        return (f'<div class="pm pask"><b>{text}</b><span>{esc(st.get("detail", ""))}</span>'
                f'<em class="pallow">Allow</em></div>')
    return f'<div class="pm psay"><i class="spark"></i><span>{text}</span></div>'


def phone(bid, b, s, dur, rel, i):
    steps = b.get("steps", [])
    title = esc(b.get("title", "השיחה במחשב"))
    msgs = "".join(_msg(st) for st in steps)
    left = PHONE_LEFT
    h = (f'<div class="in" style="padding:0"><div class="phone" id="{bid}-ph" style="left:{left}px;top:{PHONE_TOP}px;'
         f'width:{PHONE_W}px;height:{PHONE_H}px"><i class="notch"></i>'
         f'<div class="phd"><span class="pt">Code</span><span class="ps"><i class="pc">🖥️</i>{title}<i class="live"></i></span></div>'
         f'<div class="pmsgs">{msgs}</div><div class="pin">כתבו הודעה…</div></div>'
         f'<div class="pside"><h2 class="h2 gold pht">{title}</h2><div class="body psub">{esc(b.get("sub", ""))}</div></div></div>')
    js = [f'tl.fromTo(R.querySelector("#{bid}-ph"), {{ opacity: 0, y: 80, rotationY: -28, transformPerspective: 1600 }}, '
          f'{{ opacity: 1, y: 0, rotationY: 0, duration: 0.9, ease: "power3.out" }}, {s});',
          f'tl.fromTo(R.querySelector("#{bid} .live"), {{ scale: 0.7 }}, {{ scale: 1.3, duration: 0.6, yoyo: true, '
          f'repeat: {max(1, int(dur / 0.6) - 1)}, ease: "sine.inOut", immediateRender: false }}, {s + 0.5});']
    n_ask = 0
    for k, t in enumerate(times(rel, len(steps), s + 0.9, STEP_GAP)):
        js.append(f'K.in(tl, R, [{q(bid, ".pm", k)}], {t}, {{ y: 24, dur: 0.45 }});')
        sfx.ev("pop", t)
        if steps[k]["k"] == "ask":
            js.append(f'K.pop(tl, R, [{q(bid, ".pallow", n_ask)}], {round(t + 1.0, 2)}, {{ overshoot: 3 }});')
            n_ask += 1
    js.append(f'K.in(tl, R, "#{bid} .pht", {s + 0.5}, {{ x: 50, y: 0 }});')
    if b.get("sub"):
        js.append(f'K.in(tl, R, "#{bid} .psub", {s + 1.2}, {{ y: 20 }});')
    return h, js + breathe(bid, ".phone", s + 1.5, dur - 2, 1.012)


RENDER = {"phone": phone}

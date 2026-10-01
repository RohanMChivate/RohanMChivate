#!/usr/bin/env python3
"""
scripts/make_wordmark_svg.py
Render "ROHAN" as an EXTRUDED 3D wordmark rasterized to ASCII, and emit it as an
SVG that animates on GitHub (pure SMIL -- wipes in, then rocks on vertical axis).

Referenced from https://github.com/AVIVASHISHTA29
"""

import argparse
import html
import math
import os
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))


def find_default_font():
    env_font = os.environ.get("WORDMARK_FONT")
    if env_font and os.path.exists(env_font):
        return env_font, int(os.environ.get("WORDMARK_FONT_INDEX", 0))

    candidates = [
        ("C:/Windows/Fonts/arialbd.ttf", 0),
        ("C:/Windows/Fonts/segoeuib.ttf", 0),
        ("/System/Library/Fonts/Futura.ttc", 2),
        ("/System/Library/Fonts/HelveticaNeue.ttc", 0),
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 0),
        ("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 0),
    ]
    for path, idx in candidates:
        if os.path.exists(path):
            return path, idx
    return "arial.ttf", 0


DEFAULT_FONT_PATH, DEFAULT_FONT_INDEX = find_default_font()
FONT_PATH = DEFAULT_FONT_PATH
FONT_INDEX = DEFAULT_FONT_INDEX

COLS = int(os.environ.get("WORDMARK_COLS", 72))
ROW_MARGIN = int(os.environ.get("WORDMARK_ROW_MARGIN", 3))
CELL_W = 6.2
CELL_H = 10.4

TEXT = os.environ.get("WORDMARK_TEXT", "ROHAN")
USER_HANDLE = os.environ.get("WORDMARK_USER", "rohan")

MASK_H = 360
TRACKING = 0.12
LINE_GAP = 1.20
DEPTH_FRAC = 0.32
TILT_DEG = float(os.environ.get("WORDMARK_TILT", 4.0))

CAM_DIST = 6.0
FOCAL = 4.15
FIT = 0.92

RAMP = " .`:-=+*csS#%@"
LIGHT = np.array([-0.15, -0.45, -1.00])
LIGHT = LIGHT / np.linalg.norm(LIGHT)
AMBIENT = 0.18
FOG = 0.34
FOG_SPAN = 0.55

BG = "#0d1117"
BG2 = "#111722"
FRAME = "#30363d"
TITLE_TEXT = "#7d8590"
INK = "#8b949e"

PAD = 18
TITLEBAR_H = 28


def build_shell():
    """Rasterize TEXT, then return (points Nx3, normals Nx3) for its surface."""
    probe = TEXT.replace("\n", "")
    font_size = MASK_H
    for _ in range(40):
        try:
            font = ImageFont.truetype(FONT_PATH, font_size, index=FONT_INDEX)
        except Exception:
            font = ImageFont.load_default()
            break
        l, t, r, b = font.getbbox(probe)
        if b - t <= MASK_H:
            break
        font_size = int(font_size * 0.92)
    h = b - t
    track = int(round(TRACKING * font_size))
    lines = TEXT.split("\n")
    line_h = int(round(h * LINE_GAP))

    def line_w(s):
        return sum(font.getlength(c) for c in s) + track * (len(s) - 1)

    total_w = int(round(max(line_w(s) for s in lines))) + 8
    total_h = line_h * (len(lines) - 1) + h + 8
    img = Image.new("L", (total_w, total_h), 0)
    d = ImageDraw.Draw(img)
    for li, s in enumerate(lines):
        pen = 4.0 + (total_w - 8 - line_w(s)) / 2.0
        base = -t + 4 + li * line_h
        for ch in s:
            d.text((pen, base), ch, font=font, fill=255)
            pen += font.getlength(ch) + track
    mask = np.array(img) > 127
    xs_any = np.nonzero(mask.any(0))[0]
    ys_any = np.nonzero(mask.any(1))[0]
    mask = mask[ys_any[0]:ys_any[-1] + 1, xs_any[0]:xs_any[-1] + 1]

    H, W = mask.shape
    depth = max(4, int(round(H * DEPTH_FRAC)))

    cy, cx = np.nonzero(mask)

    pts, nrm = [], []
    front = np.stack([cx, cy, np.full_like(cx, -0.6, dtype=float)], 1)
    pts.append(front)
    nrm.append(np.tile([0.0, 0.0, -1.0], (len(front), 1)))
    back = np.stack([cx, cy, np.full_like(cx, depth)], 1).astype(float)
    pts.append(back)
    nrm.append(np.tile([0.0, 0.0, 1.0], (len(back), 1)))

    pad = np.pad(mask, 1)
    empty_r = ~pad[1:-1, 2:]
    empty_l = ~pad[1:-1, :-2]
    empty_d = ~pad[2:, 1:-1]
    empty_u = ~pad[:-2, 1:-1]
    edge = mask & (empty_r | empty_l | empty_d | empty_u)
    ey, ex = np.nonzero(edge)
    nx = empty_r[ey, ex].astype(float) - empty_l[ey, ex].astype(float)
    ny = empty_d[ey, ex].astype(float) - empty_u[ey, ex].astype(float)
    ln = np.sqrt(nx * nx + ny * ny)
    ln[ln == 0] = 1.0
    nx, ny = nx / ln, ny / ln
    zsteps = np.linspace(0, depth, max(3, depth // 2))
    for z in zsteps:
        pts.append(np.stack([ex, ey, np.full_like(ex, z, dtype=float)], 1))
        nrm.append(np.stack([nx, ny, np.zeros_like(nx)], 1))

    P = np.concatenate(pts, 0)
    N = np.concatenate(nrm, 0)

    P[:, 0] -= W / 2.0
    P[:, 1] -= H / 2.0
    P[:, 2] -= depth / 2.0

    scale = 1.0 / W
    P *= scale

    return P, N


def project(P, N, yaw_rad):
    tilt = math.radians(TILT_DEG)
    cx, sx = math.cos(tilt), math.sin(tilt)
    cy, sy = math.cos(yaw_rad), math.sin(yaw_rad)

    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    x1 = x * cy + z * sy
    y1 = y
    z1 = -x * sy + z * cy

    X = x1
    Y = y1 * cx - z1 * sx
    Z = y1 * sx + z1 * cx

    nx, ny, nz = N[:, 0], N[:, 1], N[:, 2]
    nx1 = nx * cy + nz * sy
    ny1 = ny
    nz1 = -nx * sy + nz * cy
    NX = nx1
    NY = ny1 * cx - nz1 * sx
    NZ = ny1 * sx + nz1 * cx

    Z_cam = Z + CAM_DIST
    u = FOCAL * X / Z_cam
    v = FOCAL * Y / Z_cam

    cos_theta = np.clip(NX * LIGHT[0] + NY * LIGHT[1] + NZ * LIGHT[2], 0.0, 1.0)
    shade = AMBIENT + (1.0 - AMBIENT) * cos_theta

    z_norm = (Z - Z.min()) / max(1e-5, (Z.max() - Z.min()))
    fog = 1.0 - FOG * np.clip(z_norm / FOG_SPAN, 0.0, 1.0)
    shade = np.clip(shade * fog, 0.0, 1.0)

    return np.stack([u, v, Z_cam, shade], 1)


def fit(frames_proj):
    all_u = np.concatenate([f[:, 0] for f in frames_proj])
    all_v = np.concatenate([f[:, 1] for f in frames_proj])
    umin, umax = all_u.min(), all_u.max()
    vmin, vmax = all_v.min(), all_v.max()

    span_u = umax - umin
    span_v = vmax - vmin

    char_aspect = CELL_H / CELL_W
    grid_w = COLS * FIT
    grid_h = grid_w * (span_v / span_u) * char_aspect
    scale = grid_w / span_u

    cx = (umin + umax) / 2.0
    cy = (vmin + vmax) / 2.0
    return scale, cx, cy


def rasterize(proj, scale, cx, cy):
    char_aspect = CELL_H / CELL_W
    u, v, z, shade = proj[:, 0], proj[:, 1], proj[:, 2], proj[:, 3]

    gx = (u - cx) * scale + COLS / 2.0
    gy = (v - cy) * scale * char_aspect

    ix = np.round(gx).astype(int)
    iy = np.round(gy).astype(int)

    valid = (ix >= 0) & (ix < COLS)
    ix, iy, z, shade = ix[valid], iy[valid], z[valid], shade[valid]

    iy_min, iy_max = iy.min(), iy.max()
    rows = iy_max - iy_min + 1 + 2 * ROW_MARGIN
    iy_shifted = iy - iy_min + ROW_MARGIN

    zbuf = np.full((rows, COLS), np.inf)
    sbuf = np.zeros((rows, COLS))

    order = np.argsort(z)[::-1]
    for idx in order:
        r = iy_shifted[idx]
        c = ix[idx]
        zv = z[idx]
        if zv <= zbuf[r, c]:
            zbuf[r, c] = zv
            sbuf[r, c] = shade[idx]

    ramp_len = len(RAMP)
    text_rows = []
    for r in range(rows):
        line = []
        for c in range(COLS):
            if np.isinf(zbuf[r, c]):
                line.append(" ")
            else:
                line.append("s")
        text_rows.append("".join(line))
    return text_rows


def emit(frames, mode, out, dur, reveal):
    rows_n = len(frames[0])
    art_w = COLS * CELL_W
    art_h = rows_n * CELL_H
    canvas_w = art_w + 2 * PAD
    canvas_h = TITLEBAR_H + art_h + PAD * 0.6
    art_top = TITLEBAR_H + PAD * 0.3
    fs = CELL_H * 0.92
    n = len(frames)

    p = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{canvas_w:.0f}" height="{canvas_h:.0f}" '
        f'viewBox="0 0 {canvas_w:.0f} {canvas_h:.0f}" font-family="ui-monospace, SFMono-Regular, '
        f'Menlo, Consolas, monospace">',
        '<defs><linearGradient id="wbg" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/>'
        '</linearGradient></defs>',
        f'<rect width="{canvas_w:.0f}" height="{canvas_h:.0f}" rx="12" fill="url(#wbg)"/>',
        f'<rect x="0.5" y="0.5" width="{canvas_w-1:.0f}" height="{canvas_h-1:.0f}" rx="12" '
        f'fill="none" stroke="{FRAME}" stroke-width="1"/>',
        f'<line x1="0" y1="{TITLEBAR_H}" x2="{canvas_w:.0f}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>',
    ]
    for i, dot in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        p.append(f'<circle cx="{PAD + i*15}" cy="{TITLEBAR_H/2}" r="4.5" fill="{dot}"/>')
    p.append(f'<text x="{canvas_w/2:.0f}" y="{TITLEBAR_H/2 + 4:.0f}" fill="{TITLE_TEXT}" '
             f'font-size="11.5" text-anchor="middle">{USER_HANDLE}@github: ~$ ./wordmark.sh --3d</text>')

    def frame_g(rows, extra=""):
        out_rows = []
        for ry, line in enumerate(rows):
            s = line.rstrip()
            if not s.strip():
                continue
            lead = len(s) - len(s.lstrip(" "))
            body = s[lead:]
            x = PAD + lead * CELL_W
            y = art_top + ry * CELL_H + CELL_H * 0.78
            out_rows.append(
                f'<text xml:space="preserve" x="{x:.1f}" y="{y:.1f}" font-size="{fs:.1f}" '
                f'textLength="{len(body)*CELL_W:.1f}" lengthAdjust="spacing">{html.escape(body)}</text>'
            )
        return f'<g fill="{INK}"{extra}>' + "".join(out_rows) + "</g>"

    if mode == "static":
        p.append(frame_g(frames[0]))
        p.append("</svg>")
        with open(out, "w", encoding="utf-8") as fh:
            fh.write("".join(p))
        print(f"wrote {out}")
        return

    # Left-to-right wipe
    p.append(f'<clipPath id="wipe"><rect x="{PAD}" y="{art_top:.1f}" height="{art_h:.1f}" width="0">'
             f'<animate attributeName="width" from="0" to="{art_w:.0f}" begin="0s" '
             f'dur="{reveal:.2f}s" fill="freeze"/></rect></clipPath>')
    p.append(f'<g clip-path="url(#wipe)">{frame_g(frames[0])}'
             f'<set attributeName="opacity" to="0" begin="{reveal:.2f}s"/></g>')
    p.append(f'<rect x="{PAD}" y="{art_top+2:.1f}" width="{CELL_W*1.6:.1f}" height="{art_h-4:.1f}" '
             f'fill="{INK}" opacity="0.16">'
             f'<animate attributeName="x" from="{PAD}" to="{PAD+art_w:.0f}" begin="0s" '
             f'dur="{reveal:.2f}s" fill="freeze"/>'
             f'<set attributeName="opacity" to="0" begin="{reveal:.2f}s"/></rect>')

    if mode == "once":
        step = dur / n
        for i, rows in enumerate(frames):
            begin = reveal + i * step
            sets = f'<set attributeName="opacity" to="1" begin="{begin:.3f}s"/>'
            if i != n - 1:
                sets += f'<set attributeName="opacity" to="0" begin="{begin+step:.3f}s"/>'
            p.append(frame_g(rows, ' opacity="0"').replace("</g>", sets + "</g>"))
    else:
        # rock: cycle the flipbook
        for i, rows in enumerate(frames):
            if i == 0:
                vals, kt = "1;0", f"0;{1/n:.5f}"
            else:
                vals, kt = "0;1;0", f"0;{i/n:.5f};{(i+1)/n:.5f}"
            anim = (f'<animate attributeName="opacity" calcMode="discrete" values="{vals}" '
                    f'keyTimes="{kt}" dur="{dur:.2f}s" begin="{reveal:.2f}s" '
                    f'repeatCount="indefinite"/>')
            p.append(frame_g(rows, ' opacity="0"').replace("</g>", anim + "</g>"))

    p.append("</svg>")
    svg = "".join(p)
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(svg)
    print(f"[SUCCESS] Wrote {out} ({len(svg)/1024:.1f} KB, {n} frames, {canvas_w:.0f}x{canvas_h:.0f})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["spin", "once", "rock", "static"], default="rock")
    ap.add_argument("--out", default="wordmark.svg")
    ap.add_argument("--text", default=None)
    ap.add_argument("--frames", type=int, default=None)
    ap.add_argument("--dur", type=float, default=None)
    ap.add_argument("--reveal", type=float, default=1.6)
    ap.add_argument("--preview", action="store_true")
    a = ap.parse_args()

    global TEXT
    if a.text:
        TEXT = a.text

    P, N = build_shell()
    rest = math.radians(-13)
    if a.mode == "spin":
        nf = a.frames or 36
        yaws = [rest + 2 * math.pi * i / nf for i in range(nf)]
        dur = a.dur or 7.0
    elif a.mode == "once":
        nf = a.frames or 32
        yaws = [rest + 2 * math.pi * i / nf for i in range(nf)] + [rest]
        dur = a.dur or 3.6
    else:  # rock
        nf = a.frames or 20
        amp = math.radians(11)
        yaws = [rest + amp * math.sin(2 * math.pi * i / nf) for i in range(nf)]
        dur = a.dur or 5.0

    proj = [project(P, N, y) for y in yaws]
    scale, cx, cy = fit(proj)
    frames = [rasterize(q, scale, cx, cy) for q in proj]

    if a.preview:
        for row in frames[0]:
            print(row.rstrip())
        return

    emit(frames, a.mode, a.out, dur, a.reveal)


if __name__ == "__main__":
    main()

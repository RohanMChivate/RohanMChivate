#!/usr/bin/env python3
"""
scripts/make_ascii_svg.py
Converts source-prepped.png into an animated, GitHub terminal-themed ASCII SVG portrait.

Implementation:
- Downsamples source-prepped.png to ~70 cols with monospace height-ratio 0.55.
- Density ramp: " .`:-=+*cs#%@" where spaces clear out pure white areas.
- Styled with GitHub terminal dark theme (#0d1117 background, #8b949e monochrome text, monospace fonts).
- Row-by-row horizontal typing animation using staggered SMIL <clipPath> wipes with fill="freeze".
- Outputs avi-ascii.svg.
"""

import os
import html
import argparse
from PIL import Image

RAMP = " .`:-=+*cs#%@"


def generate_ascii_art(image_path: str = "source-prepped.png", cols: int = 70, height_ratio: float = 0.55) -> list[str]:
    """Reads grayscale image and converts it into a list of ASCII character rows."""
    if not os.path.exists(image_path):
        import subprocess
        print(f"[!] '{image_path}' not found. Generating via prep_photo.py...")
        subprocess.run(["python", "scripts/prep_photo.py", "--output", image_path], check=True)

    img = Image.open(image_path).convert("L")
    orig_w, orig_h = img.size

    target_w = cols
    target_h = int((orig_h / orig_w) * cols * height_ratio)
    target_h = max(10, target_h)

    resized = img.resize((target_w, target_h), Image.Resampling.LANCZOS)

    ascii_rows = []
    ramp_len = len(RAMP)

    for y in range(target_h):
        row_chars = []
        for x in range(target_w):
            pixel = resized.getpixel((x, y))
            # Inverted mapping: pure white (255) -> index 0 (space ' ')
            # Pure dark (0) -> index ramp_len - 1 ('@')
            idx = int((255 - pixel) / 255.0 * (ramp_len - 1))
            idx = max(0, min(ramp_len - 1, idx))
            row_chars.append(RAMP[idx])
        ascii_rows.append("".join(row_chars))

    return ascii_rows


def build_animated_svg(ascii_rows: list[str], output_path: str = "avi-ascii.svg"):
    num_rows = len(ascii_rows)
    num_cols = len(ascii_rows[0]) if num_rows > 0 else 70

    char_w = 6.2
    char_h = 11.0
    font_size = 9.5
    padding_x = 20
    header_h = 40
    footer_h = 32

    content_w = num_cols * char_w
    content_h = num_rows * char_h

    svg_w = int(max(460, content_w + padding_x * 2))
    svg_h = int(header_h + content_h + footer_h + 16)

    start_x = (svg_w - content_w) / 2
    start_y = header_h + 16

    # Typing speed calculation
    row_dur = 0.05  # Duration for each row wipe
    step_delay = 0.04  # Delay between consecutive row starts

    svg_lines = []
    svg_lines.append(f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_w} {svg_h}" width="100%" height="100%" style="background: transparent; font-family: ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Monaco, Consolas, monospace;">
  <defs>
    <!-- Border Gradient -->
    <linearGradient id="term-border" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#30363d" />
      <stop offset="50%" stop-color="#484f58" />
      <stop offset="100%" stop-color="#30363d" />
    </linearGradient>''')

    # Add clipPath for each row with SMIL wipe animation
    for i in range(num_rows):
        row_y = start_y + i * char_h
        begin_t = round(i * step_delay, 3)
        clip_y = row_y - font_size - 1
        clip_h = char_h + 2
        svg_lines.append(f'''    <clipPath id="wipe-row-{i}">
      <rect x="{start_x - 4:.1f}" y="{clip_y:.1f}" width="0" height="{clip_h:.1f}">
        <animate attributeName="width" from="0" to="{content_w + 8:.1f}" dur="{row_dur}s" begin="{begin_t}s" fill="freeze" />
      </rect>
    </clipPath>''')

    svg_lines.append(f'''  </defs>

  <style>
    @keyframes cursor-blink {{
      0%, 49% {{ opacity: 1; }}
      50%, 100% {{ opacity: 0; }}
    }}
    .cursor {{
      animation: cursor-blink 1s infinite;
    }}
    .ascii-text {{
      fill: #8b949e;
      font-size: {font_size}px;
      font-weight: 500;
      letter-spacing: 0px;
    }}
  </style>

  <!-- Terminal Frame -->
  <rect x="2" y="2" width="{svg_w - 4}" height="{svg_h - 4}" rx="8" ry="8" fill="#0d1117" stroke="url(#term-border)" stroke-width="1.5" />

  <!-- Terminal Titlebar -->
  <path d="M 2 10 Q 2 2 10 2 L {svg_w - 10} 2 Q {svg_w - 2} 2 {svg_w - 2} 10 L {svg_w - 2} {header_h} L 2 {header_h} Z" fill="#161b22" />
  <line x1="2" y1="{header_h}" x2="{svg_w - 2}" y2="{header_h}" stroke="#30363d" stroke-width="1" />

  <!-- macOS Traffic Light Window Buttons -->
  <circle cx="18" cy="20" r="5" fill="#ff5f56" stroke="#e0443e" stroke-width="0.5" />
  <circle cx="34" cy="20" r="5" fill="#ffbd2e" stroke="#dea123" stroke-width="0.5" />
  <circle cx="50" cy="20" r="5" fill="#27c93f" stroke="#1aab29" stroke-width="0.5" />

  <!-- Titlebar Label -->
  <text x="{svg_w / 2}" y="24" fill="#8b949e" font-size="11" font-weight="500" text-anchor="middle">
    user@github: ~/avatar.ascii
  </text>

  <!-- ASCII Art Body with Staggered Horizontal Typing SMIL Wipes -->
  <g class="ascii-text">''')

    for i, row in enumerate(ascii_rows):
        row_y = start_y + i * char_h
        escaped_row = html.escape(row)
        svg_lines.append(f'    <text x="{start_x:.1f}" y="{row_y:.1f}" clip-path="url(#wipe-row-{i})" xml:space="preserve">{escaped_row}</text>')

    prompt_y = start_y + num_rows * char_h + 14
    total_anim_time = round(num_rows * step_delay + row_dur, 2)

    svg_lines.append(f'''  </g>

  <!-- Divider -->
  <line x1="16" y1="{prompt_y - 8}" x2="{svg_w - 16}" y2="{prompt_y - 8}" stroke="#21262d" stroke-width="1" />

  <!-- Terminal Bottom Prompt -->
  <text x="20" y="{prompt_y + 10}" fill="#58a6ff" font-size="11" font-weight="600">user@github</text>
  <text x="96" y="{prompt_y + 10}" fill="#8b949e" font-size="11">:</text>
  <text x="104" y="{prompt_y + 10}" fill="#7ee787" font-size="11">~</text>
  <text x="114" y="{prompt_y + 10}" fill="#c9d1d9" font-size="11">$ ./whoami.sh</text>

  <!-- Prompt Blinking Cursor -->
  <rect x="206" y="{prompt_y}" width="7" height="12" fill="#58a6ff" class="cursor">
    <animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.49;0.5;1" dur="1s" begin="{total_anim_time}s" repeatCount="indefinite" />
  </rect>
</svg>''')

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(svg_lines))

    print(f"[SUCCESS] Exported animated ASCII SVG to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Convert prepped image to animated ASCII SVG.")
    parser.add_argument("--input", "-i", default="source-prepped.png", help="Input image (default: source-prepped.png)")
    parser.add_argument("--output", "-o", default="avi-ascii.svg", help="Output SVG (default: avi-ascii.svg)")
    parser.add_argument("--cols", "-c", type=int, default=70, help="Character columns (default: 70)")
    parser.add_argument("--ratio", "-r", type=float, default=0.55, help="Height aspect ratio (default: 0.55)")
    args = parser.parse_args()

    rows = generate_ascii_art(args.input, cols=args.cols, height_ratio=args.ratio)
    build_animated_svg(rows, args.output)


if __name__ == "__main__":
    main()

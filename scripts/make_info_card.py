#!/usr/bin/env python3
"""
scripts/make_info_card.py
Generates info-card.svg styled as a Neofetch/Fastfetch output panel.

Implementation:
- Terminal window bar with macOS/Linux traffic light buttons (red, yellow, green).
- Key-value rows (User, OS, Role, Stack, Focus, Editor, Location).
- Colored keys (#58a6ff) and values (#c9d1d9).
- Staggered CSS @keyframes fadeIn animations per line.
"""

import os
import argparse
import html

DEFAULT_SPECS = [
    ("User", "developer@github"),
    ("OS", "Arch Linux x86_64 / Linux 6.11.0-zen"),
    ("Role", "Senior Systems & Full-Stack Architect"),
    ("Stack", "Python, TypeScript, Rust, Go, SQL, React"),
    ("Focus", "Distributed Systems, Low-Latency Web, Autonomous CI"),
    ("Editor", "Neovim / VS Code"),
    ("Location", "UTC / Remote"),
]


def generate_info_card(specs: list[tuple[str, str]], output_path: str = "info-card.svg"):
    svg_w = 490
    header_h = 38
    row_h = 28
    start_y = header_h + 30
    content_h = len(specs) * row_h
    svg_h = int(start_y + content_h + 60)

    # Build staggered CSS animations
    css_rules = [
        "@keyframes fadeIn {",
        "  0% { opacity: 0; transform: translateY(3px); }",
        "  100% { opacity: 1; transform: translateY(0); }",
        "}",
        "@keyframes blink {",
        "  0%, 49% { opacity: 1; }",
        "  50%, 100% { opacity: 0; }",
        "}",
        ".cursor { animation: blink 1s infinite; }",
    ]

    for idx in range(len(specs)):
        delay = round(0.15 + idx * 0.12, 2)
        css_rules.append(f".line-{idx} {{ animation: fadeIn 0.4s ease forwards; animation-delay: {delay}s; opacity: 0; }}")

    svg_lines = []
    svg_lines.append(f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_w} {svg_h}" width="100%" height="100%" style="background: transparent; font-family: ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Monaco, Consolas, monospace;">
  <defs>
    <linearGradient id="card-border" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#30363d" />
      <stop offset="50%" stop-color="#58a6ff" stop-opacity="0.4" />
      <stop offset="100%" stop-color="#30363d" />
    </linearGradient>
  </defs>

  <style>
    {chr(10).join("    " + r for r in css_rules)}
    .key-text {{
      fill: #58a6ff;
      font-size: 12px;
      font-weight: 600;
    }}
    .val-text {{
      fill: #c9d1d9;
      font-size: 12px;
      font-weight: 400;
    }}
  </style>

  <!-- Terminal Window Background -->
  <rect x="2" y="2" width="{svg_w - 4}" height="{svg_h - 4}" rx="8" ry="8" fill="#0d1117" stroke="url(#card-border)" stroke-width="1.5" />

  <!-- Window Header Bar -->
  <path d="M 2 10 Q 2 2 10 2 L {svg_w - 10} 2 Q {svg_w - 2} 2 {svg_w - 2} 10 L {svg_w - 2} {header_h} L 2 {header_h} Z" fill="#161b22" />
  <line x1="2" y1="{header_h}" x2="{svg_w - 2}" y2="{header_h}" stroke="#30363d" stroke-width="1" />

  <!-- macOS / Linux Traffic Light Buttons -->
  <circle cx="18" cy="19" r="5" fill="#ff5f56" stroke="#e0443e" stroke-width="0.5" />
  <circle cx="34" cy="19" r="5" fill="#ffbd2e" stroke="#dea123" stroke-width="0.5" />
  <circle cx="50" cy="19" r="5" fill="#27c93f" stroke="#1aab29" stroke-width="0.5" />

  <!-- Header Title -->
  <text x="{svg_w / 2}" y="23" fill="#8b949e" font-size="11" font-weight="500" text-anchor="middle">
    fastfetch --profile ~/.config/fastfetch/config.jsonc
  </text>

  <!-- Decorative Host Pill -->
  <rect x="{svg_w - 88}" y="10" width="72" height="18" rx="4" fill="#1f242c" stroke="#30363d" stroke-width="0.8" />
  <circle cx="{svg_w - 78}" cy="19" r="3" fill="#39d353" />
  <text x="{svg_w - 70}" y="22" fill="#7ee787" font-size="8.5" font-weight="600">ONLINE</text>

  <!-- Key-Value Rows with Staggered FadeIn -->
  <g transform="translate(26, {start_y})">''')

    for idx, (k, v) in enumerate(specs):
        y_pos = idx * row_h
        esc_k = html.escape(k)
        esc_v = html.escape(v)
        delay_t = round(0.15 + idx * 0.12, 2)
        svg_lines.append(f'''    <g class="line-{idx}">
      <text x="0" y="{y_pos}" class="key-text">{esc_k}</text>
      <text x="82" y="{y_pos}" fill="#8b949e" font-size="11">›</text>
      <text x="98" y="{y_pos}" class="val-text">{esc_v}</text>
      <animate attributeName="opacity" from="0" to="1" dur="0.4s" begin="{delay_t}s" fill="freeze" />
    </g>''')

    prompt_y = len(specs) * row_h + 16

    svg_lines.append(f'''  </g>

  <!-- Divider Line -->
  <line x1="24" y1="{start_y + prompt_y - 12}" x2="{svg_w - 24}" y2="{start_y + prompt_y - 12}" stroke="#21262d" stroke-width="1" />

  <!-- Terminal Color Swatches (Neofetch Classic ANSI) -->
  <g transform="translate(26, {start_y + prompt_y + 2})">
    <rect x="0" y="0" width="20" height="9" rx="2" fill="#161b22" stroke="#30363d" stroke-width="0.5" />
    <rect x="24" y="0" width="20" height="9" rx="2" fill="#ff5f56" />
    <rect x="48" y="0" width="20" height="9" rx="2" fill="#27c93f" />
    <rect x="72" y="0" width="20" height="9" rx="2" fill="#ffbd2e" />
    <rect x="96" y="0" width="20" height="9" rx="2" fill="#58a6ff" />
    <rect x="120" y="0" width="20" height="9" rx="2" fill="#bc8cff" />
    <rect x="144" y="0" width="20" height="9" rx="2" fill="#39c5cf" />
    <rect x="168" y="0" width="20" height="9" rx="2" fill="#c9d1d9" />

    <!-- Terminal Prompt with Blinking Cursor -->
    <text x="{svg_w - 134}" y="9" fill="#58a6ff" font-size="10.5" font-weight="600">user@github</text>
    <rect x="{svg_w - 60}" y="0" width="6" height="10" fill="#58a6ff" class="cursor">
      <animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.49;0.5;1" dur="1s" repeatCount="indefinite" />
    </rect>
  </g>
</svg>''')

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(svg_lines))

    print(f"[SUCCESS] Exported info card SVG to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Generate info card SVG.")
    parser.add_argument("--output", "-o", default="info-card.svg", help="Output SVG path (default: info-card.svg)")
    parser.add_argument("--user", default="developer@github")
    parser.add_argument("--os", default="Arch Linux x86_64 / Linux 6.11.0-zen")
    parser.add_argument("--role", default="Senior Systems & Full-Stack Architect")
    parser.add_argument("--stack", default="Python, TypeScript, Rust, Go, SQL, React")
    parser.add_argument("--focus", default="Distributed Systems, Low-Latency Web, Autonomous CI")
    parser.add_argument("--editor", default="Neovim / VS Code")
    parser.add_argument("--location", default="UTC / Remote")
    args = parser.parse_args()

    specs = [
        ("User", args.user),
        ("OS", args.os),
        ("Role", args.role),
        ("Stack", args.stack),
        ("Focus", args.focus),
        ("Editor", args.editor),
        ("Location", args.location),
    ]

    generate_info_card(specs, args.output)


if __name__ == "__main__":
    main()

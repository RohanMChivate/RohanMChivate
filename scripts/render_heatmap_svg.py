#!/usr/bin/env python3
"""
scripts/render_heatmap_svg.py
Renders contrib-heatmap.svg from data/contributions.json.

Implementation:
- Reads data/contributions.json (aligned to 53 weeks / 371 days).
- Palette: ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"].
- Diagonal drop-in reveal animation: CSS keyframes on each cell with dynamic
  animation-delay: (col + row) * 0.015s.
- Outputs contrib-heatmap.svg.
"""

import os
import json
import argparse
from datetime import datetime

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]


def load_contributions_data(path: str = "data/contributions.json") -> dict:
    if not os.path.exists(path):
        import subprocess
        print(f"[!] '{path}' not found. Calling fetch_contributions.py...")
        subprocess.run(["python", "scripts/fetch_contributions.py", "--output", path], check=True)

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def render_heatmap(data: dict, output_path: str = "contrib-heatmap.svg"):
    contributions = data.get("contributions", [])
    username = data.get("username", "developer")
    total_contribs = data.get("total_contributions", 0)
    current_streak = data.get("current_streak", 0)
    longest_streak = data.get("longest_streak", 0)

    # 53 weeks x 7 days
    num_cols = 53
    num_rows = 7

    cell_size = 10.5
    cell_gap = 3.5
    cell_step = cell_size + cell_gap

    matrix_w = num_cols * cell_step
    matrix_h = num_rows * cell_step

    margin_left = 64
    margin_top = 108

    svg_w = int(max(860, margin_left + matrix_w + 32))
    svg_h = 248
    header_h = 38

    # Month label positions
    months_seen = set()
    month_labels = []
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    # Slice into weeks
    weeks = []
    for c in range(num_cols):
        week_days = contributions[c * 7: (c + 1) * 7]
        weeks.append(week_days)
        for day in week_days:
            try:
                dt = datetime.strptime(day["date"], "%Y-%m-%d")
                m_key = f"{dt.year}-{dt.month}"
                if m_key not in months_seen and dt.day <= 14:
                    months_seen.add(m_key)
                    month_labels.append((month_names[dt.month - 1], c))
                    break
            except Exception:
                pass

    svg_lines = []
    svg_lines.append(f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_w} {svg_h}" width="100%" height="100%" style="background: transparent; font-family: ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Monaco, Consolas, monospace;">
  <defs>
    <linearGradient id="term-border" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#30363d" />
      <stop offset="50%" stop-color="#238636" stop-opacity="0.4" />
      <stop offset="100%" stop-color="#30363d" />
    </linearGradient>
  </defs>

  <style>
    @keyframes dropIn {{
      0% {{
        opacity: 0;
        transform: translateY(-8px) scale(0.4);
      }}
      70% {{
        transform: translateY(1px) scale(1.08);
      }}
      100% {{
        opacity: 1;
        transform: translateY(0) scale(1);
      }}
    }}
    @keyframes blink {{
      0%, 49% {{ opacity: 1; }}
      50%, 100% {{ opacity: 0; }}
    }}
    .cursor {{ animation: blink 1s infinite; }}
    .axis-label {{
      fill: #6e7681;
      font-size: 9.5px;
      font-weight: 500;
    }}
  </style>

  <!-- Terminal Window Background -->
  <rect x="2" y="2" width="{svg_w - 4}" height="{svg_h - 4}" rx="8" ry="8" fill="#0d1117" stroke="url(#term-border)" stroke-width="1.5" />

  <!-- Terminal Window Header -->
  <path d="M 2 10 Q 2 2 10 2 L {svg_w - 10} 2 Q {svg_w - 2} 2 {svg_w - 2} 10 L {svg_w - 2} {header_h} L 2 {header_h} Z" fill="#161b22" />
  <line x1="2" y1="{header_h}" x2="{svg_w - 2}" y2="{header_h}" stroke="#30363d" stroke-width="1" />

  <!-- macOS / Linux Traffic Light Buttons -->
  <circle cx="18" cy="19" r="5" fill="#ff5f56" stroke="#e0443e" stroke-width="0.5" />
  <circle cx="34" cy="19" r="5" fill="#ffbd2e" stroke="#dea123" stroke-width="0.5" />
  <circle cx="50" cy="19" r="5" fill="#27c93f" stroke="#1aab29" stroke-width="0.5" />

  <!-- Terminal Title -->
  <text x="{svg_w / 2}" y="23" fill="#8b949e" font-size="11" font-weight="500" text-anchor="middle">
    git log --graph --contributions (UTC)
  </text>

  <!-- Stats Telemetry Strip -->
  <g transform="translate({margin_left}, 62)">
    <text x="0" y="0" fill="#8b949e" font-size="11">Total:</text>
    <text x="42" y="0" fill="#58a6ff" font-size="11" font-weight="700">{total_contribs:,}</text>

    <text x="130" y="0" fill="#8b949e" font-size="11">Current Streak:</text>
    <text x="234" y="0" fill="#39d353" font-size="11" font-weight="700">{current_streak} days</text>

    <text x="320" y="0" fill="#8b949e" font-size="11">Longest Streak:</text>
    <text x="428" y="0" fill="#f1e05a" font-size="11" font-weight="700">{longest_streak} days</text>
  </g>

  <!-- Month Labels -->
  <g transform="translate({margin_left}, {margin_top - 12})">''')

    for m_text, col_idx in month_labels:
        x_pos = col_idx * cell_step
        svg_lines.append(f'    <text x="{x_pos:.1f}" y="0" class="axis-label">{m_text}</text>')

    svg_lines.append(f'''  </g>

  <!-- Day of Week Labels (Mon, Wed, Fri) -->
  <g transform="translate({margin_left - 30}, {margin_top})">
    <text x="0" y="{1 * cell_step + 8.5:.1f}" class="axis-label">Mon</text>
    <text x="0" y="{3 * cell_step + 8.5:.1f}" class="axis-label">Wed</text>
    <text x="0" y="{5 * cell_step + 8.5:.1f}" class="axis-label">Fri</text>
  </g>

  <!-- Contribution Squares Matrix with Diagonal Drop-in Reveal -->
  <g transform="translate({margin_left}, {margin_top})">''')

    for col in range(num_cols):
        for row in range(num_rows):
            idx = col * 7 + row
            day_data = contributions[idx] if idx < len(contributions) else {}
            level = day_data.get("data-level", 0)
            level = max(0, min(4, level))
            color = PALETTE[level]

            x_pos = col * cell_step
            y_pos = row * cell_step

            # Diagonal drop-in delay: (col + row) * 0.015s
            delay_sec = round((col + row) * 0.015, 4)
            center_x = round(x_pos + cell_size / 2, 1)
            center_y = round(y_pos + cell_size / 2, 1)

            date_str = day_data.get("date", "")
            cnt = day_data.get("count", 0)
            tip_title = f"{date_str}: {cnt} contributions" if cnt > 0 else f"{date_str}: No contributions"

            stroke_color = "#21262d" if level == 0 else color

            svg_lines.append(
                f'    <rect x="{x_pos:.1f}" y="{y_pos:.1f}" width="{cell_size}" height="{cell_size}" rx="2" ry="2" fill="{color}" stroke="{stroke_color}" stroke-width="0.3" '
                f'style="animation: dropIn 0.35s cubic-bezier(0.16, 1, 0.3, 1) forwards; animation-delay: {delay_sec}s; transform-origin: {center_x}px {center_y}px; opacity: 0;">'
                f'<animate attributeName="opacity" from="0" to="1" dur="0.35s" begin="{delay_sec}s" fill="freeze" />'
                f'<title>{tip_title}</title></rect>'
            )

    svg_lines.append(f'''  </g>

  <!-- Footer Command Prompt & Legend -->
  <g transform="translate(24, {svg_h - 18})">
    <!-- Prompt -->
    <text x="0" y="8" fill="#58a6ff" font-size="10.5" font-weight="600">user@github</text>
    <text x="78" y="8" fill="#8b949e" font-size="10.5">:</text>
    <text x="86" y="8" fill="#7ee787" font-size="10.5">~/graph</text>
    <text x="138" y="8" fill="#c9d1d9" font-size="10.5">$ git status --sync</text>
    <rect x="254" y="-1" width="6" height="10" fill="#58a6ff" class="cursor">
      <animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.49;0.5;1" dur="1s" repeatCount="indefinite" />
    </rect>

    <!-- Legend -->
    <g transform="translate({svg_w - 220}, 0)">
      <text x="0" y="8" fill="#6e7681" font-size="9.5" font-weight="500">Less</text>
      <rect x="30" y="-1" width="9" height="9" rx="2" fill="{PALETTE[0]}" stroke="#21262d" stroke-width="0.5" />
      <rect x="43" y="-1" width="9" height="9" rx="2" fill="{PALETTE[1]}" />
      <rect x="56" y="-1" width="9" height="9" rx="2" fill="{PALETTE[2]}" />
      <rect x="69" y="-1" width="9" height="9" rx="2" fill="{PALETTE[3]}" />
      <rect x="82" y="-1" width="9" height="9" rx="2" fill="{PALETTE[4]}" />
      <text x="98" y="8" fill="#6e7681" font-size="9.5" font-weight="500">More</text>
    </g>
  </g>
</svg>''')

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(svg_lines))

    print(f"[SUCCESS] Exported contribution heatmap SVG to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Render animated GitHub contribution heatmap SVG.")
    parser.add_argument("--data", "-d", default="data/contributions.json", help="Path to contributions JSON")
    parser.add_argument("--output", "-o", default="contrib-heatmap.svg", help="Output SVG path")
    args = parser.parse_args()

    data = load_contributions_data(args.data)
    render_heatmap(data, args.output)


if __name__ == "__main__":
    main()

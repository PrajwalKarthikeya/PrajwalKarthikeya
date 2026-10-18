#!/usr/bin/env python3
"""
GitHub Skyline Generator for Profile README
Generates both an ASCII art contribution skyline (compatible with github/gh-skyline)
and a dark-mode vector SVG card (assets/github-skyline.svg), then updates README.md.
"""

import json
import os
import sys
import subprocess
import datetime
import urllib.request
import urllib.error

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

USERNAME = os.environ.get("GITHUB_ACTOR", "PrajwalKarthikeya")
YEAR = int(os.environ.get("SKYLINE_YEAR", datetime.datetime.now().year))

def fetch_contributions(username, year):
    from_date = f"{year}-01-01T00:00:00Z"
    to_date = f"{year}-12-31T23:59:59Z"
    query = f"""
    query {{
      user(login: "{username}") {{
        contributionsCollection(from: "{from_date}", to: "{to_date}") {{
          contributionCalendar {{
            totalContributions
            weeks {{
              contributionDays {{
                date
                contributionCount
                color
              }}
            }}
          }}
        }}
      }}
    }}
    """
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    
    if token:
        # Use direct GraphQL API call
        url = "https://api.github.com/graphql"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "Skyline-Generator"
        }
        data = json.dumps({"query": query}).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers)
        with urllib.request.urlopen(req) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            return body["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    else:
        # Fall back to GitHub CLI
        cmd = ["gh", "api", "graphql", "-f", f"query={query}"]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(res.stdout)
        return data["data"]["user"]["contributionsCollection"]["contributionCalendar"]

def generate_ascii_skyline(calendar, username, year):
    weeks = calendar["weeks"]
    total = calendar["totalContributions"]
    
    max_c = 0
    for w in weeks:
        for d in w["contributionDays"]:
            if d["contributionCount"] > max_c:
                max_c = d["contributionCount"]
                
    now = datetime.datetime.now(datetime.timezone.utc)
    num_cols = len(weeks)
    ascii_grid = [[" " for _ in range(num_cols)] for _ in range(7)]
    
    EMPTY = ' '
    FUTURE = '.'
    FOUNDATION = ['░', '▒', '▓']
    MIDDLE = ['░', '▒', '▓']
    TOP = ['╻', '┃', '╽']
    
    def get_block_type(norm):
        if norm < 0.33:
            return 0
        elif norm < 0.66:
            return 1
        else:
            return 2
            
    for col_idx, w in enumerate(weeks):
        days = w["contributionDays"]
        non_zero = []
        zero_c = []
        future = []
        
        for d in days:
            d_date = datetime.datetime.strptime(d["date"], "%Y-%m-%d").replace(tzinfo=datetime.timezone.utc)
            if d_date > now:
                future.append({"count": -1, "date": d["date"]})
            elif d["contributionCount"] > 0:
                non_zero.append({"count": d["contributionCount"], "date": d["date"]})
            else:
                zero_c.append({"count": 0, "date": d["date"]})
                
        sorted_days = non_zero + zero_c + future
        non_zero_count = len(non_zero)
        
        max_day_idx = min(7, len(sorted_days))
        for day_idx in range(max_day_idx):
            item = sorted_days[day_idx]
            if item["count"] == -1:
                ascii_grid[day_idx][col_idx] = FUTURE
            elif item["count"] == 0:
                ascii_grid[day_idx][col_idx] = EMPTY
            else:
                norm = item["count"] / max_c if max_c > 0 else 0
                b_type = get_block_type(norm)
                if non_zero_count == 1:
                    ch = FOUNDATION[b_type]
                elif day_idx == non_zero_count - 1:
                    ch = TOP[b_type]
                elif day_idx == 0:
                    ch = FOUNDATION[b_type]
                else:
                    ch = MIDDLE[b_type]
                ascii_grid[day_idx][col_idx] = ch

    lines = [
        "           ____ _ _   _   _       _     ",
        "          / ___(_) |_| | | |_   _| |__  ",
        "         | |  _| | __| |_| | | | | '_ \\ ",
        "         | |_| | | |_|  _  | |_| | |_) |",
        "          \\____|_|\\__|_| |_|\\__,_|_.__/ ",
        "",
        "          ____  _          _ _            ",
        "         / ___|| | ___   _| (_)_ __   ___ ",
        "         \\___ \\| |/ / | | | | | '_ \\ / _ \\",
        "          ___) |   <| |_| | | | | | | __/",
        "         |____/|_|\\_\\\\__, |_|_|_| |_|\\___|",
        "                    |___/",
        ""
    ]
    
    # Skyline rows (top row 6 to bottom row 0)
    for r in range(6, -1, -1):
        lines.append("".join(ascii_grid[r]))
        
    lines.append("")
    width = 53
    user_str = username.center(width)
    year_str = f"{year} · {total} Contributions".center(width)
    lines.append(user_str)
    lines.append(year_str)
    
    return "\n".join(lines), ascii_grid, max_c

def generate_svg_skyline(calendar, username, year, ascii_grid, max_c):
    weeks = calendar["weeks"]
    total = calendar["totalContributions"]
    
    width = 880
    height = 360
    
    margin_left = 60
    grid_w = width - margin_left * 2
    col_w = grid_w / 53
    bar_w = 10
    baseline_y = 280
    max_tower_h = 140
    
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="100%" style="border-radius: 12px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif;">
  <defs>
    <!-- Background Gradient -->
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#090d16" />
      <stop offset="50%" stop-color="#0d1117" />
      <stop offset="100%" stop-color="#0a0e1a" />
    </linearGradient>

    <!-- Tower Gradients -->
    <linearGradient id="towerHigh" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#39d353" />
      <stop offset="30%" stop-color="#26a641" />
      <stop offset="100%" stop-color="#0e4429" />
    </linearGradient>

    <linearGradient id="towerMed" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#58a6ff" />
      <stop offset="40%" stop-color="#388bfd" />
      <stop offset="100%" stop-color="#1f6feb" />
    </linearGradient>

    <linearGradient id="towerLow" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#8b949e" />
      <stop offset="100%" stop-color="#30363d" />
    </linearGradient>

    <linearGradient id="towerFuture" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#21262d" />
      <stop offset="100%" stop-color="#161b22" />
    </linearGradient>

    <!-- Skyline Glow Filter -->
    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="4" result="blur" />
      <feComposite in="SourceGraphic" in2="blur" operator="over" />
    </filter>

    <filter id="spireGlow" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="2.5" result="blur" />
      <feComposite in="SourceGraphic" in2="blur" operator="over" />
    </filter>
  </defs>

  <!-- Card Frame -->
  <rect x="1" y="1" width="{width - 2}" height="{height - 2}" rx="12" fill="url(#bgGrad)" stroke="#30363d" stroke-width="1.5" />

  <!-- Background Grid Lines -->
  <g stroke="#1f242c" stroke-width="1" opacity="0.6">
    <line x1="{margin_left}" y1="{baseline_y}" x2="{width - margin_left}" y2="{baseline_y}" stroke="#388bfd" stroke-width="1.5" opacity="0.8" />
    <line x1="{margin_left}" y1="{baseline_y - 30}" x2="{width - margin_left}" y2="{baseline_y - 30}" stroke-dasharray="3,3" />
    <line x1="{margin_left}" y1="{baseline_y - 60}" x2="{width - margin_left}" y2="{baseline_y - 60}" stroke-dasharray="3,3" />
    <line x1="{margin_left}" y1="{baseline_y - 90}" x2="{width - margin_left}" y2="{baseline_y - 90}" stroke-dasharray="3,3" />
    <line x1="{margin_left}" y1="{baseline_y - 120}" x2="{width - margin_left}" y2="{baseline_y - 120}" stroke-dasharray="3,3" />
  </g>

  <!-- Header Section -->
  <g transform="translate({margin_left}, 32)">
    <path fill="#8b949e" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z" transform="scale(1.5)" />

    <text x="35" y="16" fill="#f0f6fc" font-size="16" font-weight="700" letter-spacing="1">GITHUB SKYLINE</text>
    <text x="35" y="32" fill="#8b949e" font-size="12">Contribution Architecture &middot; {username}</text>

    <!-- Stats Badges -->
    <g transform="translate({grid_w - 230}, 0)">
      <rect x="0" y="2" width="65" height="26" rx="6" fill="#161b22" stroke="#30363d" />
      <text x="32.5" y="19" fill="#58a6ff" font-size="12" font-weight="600" text-anchor="middle">{year}</text>

      <rect x="75" y="2" width="155" height="26" rx="6" fill="#161b22" stroke="#238636" />
      <circle cx="90" cy="15" r="4" fill="#39d353" />
      <text x="100" y="19" fill="#e6edf3" font-size="12" font-weight="600">{total} Contributions</text>
    </g>
  </g>

  <!-- Towers & Buildings -->
  <g>
"""
    for col_idx in range(53):
        x = margin_left + col_idx * col_w + (col_w - bar_w) / 2
        active_days = 0
        total_week_contribs = 0
        is_future_week = True
        
        for row in range(7):
            ch = ascii_grid[row][col_idx]
            if ch != '.':
                is_future_week = False
            if ch in ['░', '▒', '▓', '╻', '┃', '╽']:
                active_days += 1
                
        if col_idx < len(weeks):
            for d in weeks[col_idx]["contributionDays"]:
                total_week_contribs += d["contributionCount"]
                
        if is_future_week:
            h = 18
            y = baseline_y - h
            svg += f"""    <rect x="{x:.1f}" y="{y:.1f}" width="{bar_w}" height="{h}" rx="2" fill="url(#towerFuture)" stroke="#30363d" stroke-dasharray="2,2" opacity="0.4" />\n"""
        elif active_days == 0:
            svg += f"""    <rect x="{x:.1f}" y="{baseline_y - 2}" width="{bar_w}" height="2" fill="#21262d" rx="1" />\n"""
        else:
            scale_factor = active_days / 7.0
            intensity_boost = min(1.0, total_week_contribs / 20.0) * 30.0
            tower_h = max(14, scale_factor * (max_tower_h - 30) + intensity_boost)
            y = baseline_y - tower_h
            
            has_peak = any(ascii_grid[row][col_idx] in ['╻', '┃', '╽'] for row in range(7))
            if active_days >= 5 or total_week_contribs >= 15:
                grad_id = "towerHigh"
                stroke_color = "#39d353"
                glow_attr = 'filter="url(#glow)"'
            elif active_days >= 2:
                grad_id = "towerMed"
                stroke_color = "#58a6ff"
                glow_attr = ""
            else:
                grad_id = "towerLow"
                stroke_color = "#8b949e"
                glow_attr = ""
                
            svg += f"""    <g>
      <rect x="{x:.1f}" y="{y:.1f}" width="{bar_w}" height="{tower_h:.1f}" rx="2" fill="url(#{grad_id})" stroke="{stroke_color}" stroke-width="0.8" opacity="0.95" />\n"""
            
            num_floors = int(tower_h // 12)
            for fl in range(num_floors):
                fy = baseline_y - (fl + 1) * 12 + 2
                svg += f"""      <line x1="{x + 2:.1f}" y1="{fy:.1f}" x2="{x + bar_w - 2:.1f}" y2="{fy:.1f}" stroke="#ffffff" stroke-width="1" opacity="0.25" />\n"""

            if has_peak and tower_h > 45:
                spire_x = x + bar_w / 2
                spire_y = y - 12
                svg += f"""      <line x1="{spire_x:.1f}" y1="{y:.1f}" x2="{spire_x:.1f}" y2="{spire_y:.1f}" stroke="{stroke_color}" stroke-width="1.5" />
      <circle cx="{spire_x:.1f}" cy="{spire_y:.1f}" r="2" fill="#ff7b72" {glow_attr} />\n"""
            svg += "    </g>\n"

    svg += f"""  </g>

  <!-- Month Markers -->
  <g fill="#8b949e" font-size="10" text-anchor="middle">\n"""
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    for m_idx, m_name in enumerate(months):
        approx_week = m_idx * 4.41 + 1
        mx = margin_left + approx_week * col_w
        svg += f"""    <text x="{mx:.1f}" y="{baseline_y + 18}">{m_name}</text>\n"""

    svg += f"""  </g>

  <!-- Legend & Tagline -->
  <g transform="translate({margin_left}, {height - 24})">
    <text x="0" y="0" fill="#58a6ff" font-size="11" font-family="'JetBrains Mono', monospace">gh skyline &bull; 3D Cityscape Engine</text>

    <g transform="translate({grid_w - 360}, -4)" font-size="10" fill="#8b949e">
      <rect x="0" y="-8" width="10" height="10" rx="1" fill="#161b22" stroke="#30363d" stroke-dasharray="1,1" />
      <text x="14" y="0">Future</text>

      <rect x="65" y="-8" width="10" height="10" rx="1" fill="url(#towerLow)" />
      <text x="80" y="0">Low</text>

      <rect x="120" y="-8" width="10" height="10" rx="1" fill="url(#towerMed)" />
      <text x="135" y="0">Med</text>

      <rect x="180" y="-8" width="10" height="10" rx="1" fill="url(#towerHigh)" />
      <text x="195" y="0">High</text>

      <circle cx="255" cy="-3" r="3" fill="#ff7b72" filter="url(#spireGlow)" />
      <text x="264" y="0">Peak Spire</text>
    </g>
  </g>
</svg>
"""
    return svg

def update_readme(repo_root, ascii_art):
    readme_path = os.path.join(repo_root, "README.md")
    if not os.path.exists(readme_path):
        print(f"README.md not found at {readme_path}")
        return
        
    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()

    start_marker = "<!-- SKYLINE:START -->"
    end_marker = "<!-- SKYLINE:END -->"

    skyline_section = f"""{start_marker}
```text
{ascii_art}
```
{end_marker}"""

    if start_marker in content and end_marker in content:
        before = content.split(start_marker)[0]
        after = content.split(end_marker)[1]
        new_content = before + skyline_section + after
    else:
        # Insert before ELSEWHERE or at the end
        if "## ` ELSEWHERE`" in content:
            parts = content.split("## ` ELSEWHERE`")
            new_section = f"""## ` CONTRIBUTIONS SKYLINE`

<div align="center">

<img src="./assets/github-skyline.svg" alt="GitHub Skyline - PrajwalKarthikeya" width="100%" />

<br><br>

<details>
<summary><b>View ASCII Terminal Skyline</b></summary>

{skyline_section}

</details>

</div>

---

## ` ELSEWHERE`"""
            new_content = parts[0] + new_section + parts[1]
        else:
            new_content = content + f"\n\n## ` CONTRIBUTIONS SKYLINE`\n\n{skyline_section}\n"

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("Updated README.md with latest skyline!")

def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    assets_dir = os.path.join(repo_root, "assets")
    os.makedirs(assets_dir, exist_ok=True)
    
    print(f"Fetching contribution calendar for {USERNAME} ({YEAR})...")
    calendar = fetch_contributions(USERNAME, YEAR)
    
    print("Generating ASCII skyline...")
    ascii_art, ascii_grid, max_c = generate_ascii_skyline(calendar, USERNAME, YEAR)
    
    print("Generating SVG skyline card...")
    svg_content = generate_svg_skyline(calendar, USERNAME, YEAR, ascii_grid, max_c)
    
    svg_path = os.path.join(assets_dir, "github-skyline.svg")
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(svg_content)
    print(f"Saved SVG skyline to {svg_path}")
    
    ascii_path = os.path.join(assets_dir, "skyline.ascii.txt")
    with open(ascii_path, "w", encoding="utf-8") as f:
        f.write(ascii_art)
    print(f"Saved ASCII skyline to {ascii_path}")
    
    print("Updating README.md...")
    update_readme(repo_root, ascii_art)
    print("Skyline generation complete!")

if __name__ == "__main__":
    main()

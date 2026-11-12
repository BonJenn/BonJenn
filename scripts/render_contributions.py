"""Render GitHub's contributionCalendar JSON as light and dark SVG grids."""

import calendar
import json
import sys
from datetime import date
from html import escape
from pathlib import Path


LEVELS = ["NONE", "FIRST_QUARTILE", "SECOND_QUARTILE", "THIRD_QUARTILE", "FOURTH_QUARTILE"]
THEMES = {
    "light": ("#1f2328", "#59636e", "#1f23281a", ["#eff2f5", "#aceebb", "#4ac26b", "#2da44e", "#116329"]),
    "dark": ("#f0f6fc", "#9198a1", "#ffffff0d", ["#151b23", "#033a16", "#196c2e", "#2ea043", "#56d364"]),
}


def render(data, theme):
    foreground, muted, border, colors = THEMES[theme]
    weeks = data["weeks"]
    width = 70 + len(weeks) * 14
    total = data["totalContributions"]
    title = f"{total:,} contributions in the last year"
    days = [day for week in weeks for day in week["contributionDays"]]
    if not days:
        raise ValueError("GitHub returned an empty calendar")
    description = f"Jonathan Benn's daily GitHub contributions, {days[0]['date']} through {days[-1]['date']}."
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="190" viewBox="0 0 {width} 190" role="img" aria-labelledby="title description">',
        f'<title id="title">{escape(title)}</title>',
        f'<desc id="description">{escape(description)}</desc>',
        '<g font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif">',
        f'<text x="8" y="25" font-size="16" fill="{foreground}">{escape(title)}</text>',
    ]
    for weekday, label in [(1, "Mon"), (3, "Wed"), (5, "Fri")]:
        parts.append(f'<text x="8" y="{64 + weekday * 14 + 9}" font-size="10" fill="{muted}">{label}</text>')
    previous_month = None
    for column, week in enumerate(weeks):
        week_days = week["contributionDays"]
        if not week_days:
            continue
        first = date.fromisoformat(week_days[0]["date"])
        if first.month != previous_month:
            parts.append(f'<text x="{52 + column * 14}" y="51" font-size="10" fill="{muted}">{calendar.month_abbr[first.month]}</text>')
            previous_month = first.month
        for day in week_days:
            level = LEVELS.index(day["contributionLevel"])
            count = day["contributionCount"]
            label = f"{day['date']}: {count:,} contribution{'s' if count != 1 else ''}"
            parts.append(
                f'<rect x="{52 + column * 14}" y="{64 + day["weekday"] * 14}" width="11" height="11" rx="2" '
                f'fill="{colors[level]}" stroke="{border}"><title>{escape(label)}</title></rect>'
            )
    parts.append(f'<text x="8" y="179" font-size="10" fill="{muted}">Updated daily from GitHub</text>')
    legend_x = width - 145
    parts.append(f'<text x="{legend_x - 29}" y="179" font-size="10" fill="{muted}">Less</text>')
    for index, color in enumerate(colors):
        parts.append(f'<rect x="{legend_x + index * 14}" y="170" width="11" height="11" rx="2" fill="{color}" stroke="{border}"/>')
    parts.append(f'<text x="{legend_x + 73}" y="179" font-size="10" fill="{muted}">More</text>')
    parts.extend(["</g>", "</svg>"])
    return "\n".join(parts) + "\n"


if __name__ == "__main__":
    response = json.load(sys.stdin)
    if response.get("errors"):
        raise ValueError(response["errors"])
    data = response["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    destination = Path(__file__).resolve().parents[1] / "assets"
    destination.mkdir(exist_ok=True)
    for theme in THEMES:
        (destination / f"contributions-{theme}.svg").write_text(render(data, theme))

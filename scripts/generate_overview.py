import os
import math
from datetime import date, timedelta
from pathlib import Path
import requests

USERNAME = os.getenv("GITHUB_USERNAME", "rohityadav68403-web")
TOKEN = os.getenv("GITHUB_TOKEN")

if not TOKEN:
    raise SystemExit("GITHUB_TOKEN is required.")

HEADERS = {
    '<text x="82" y="95" text-anchor="middle" font-family="Arial" font-size="30" font-weight="700" fill="#67e8f9">RY</text>',
}

def graphql(query, variables):
    r = requests.post(
        "https://api.github.com/graphql",
        json={"query": query, "variables": variables},
        headers=HEADERS,
        timeout=30,
    )
    r.raise_for_status()
    data = r.json()
    if data.get("errors"):
        raise RuntimeError(data["errors"])
    return data["data"]

def esc(value):
    return (str(value).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))

def compact(n):
    return f"{int(n):,}"

def streaks(days):
    values = {d["date"]: int(d["contributionCount"]) for d in days}
    ordered = sorted(values)
    longest = 0
    run = 0
    previous = None

    for day in ordered:
        if values[day] > 0:
            if previous:
                a = date.fromisoformat(previous)
                b = date.fromisoformat(day)
                run = run + 1 if b == a + timedelta(days=1) else 1
            else:
                run = 1
            longest = max(longest, run)
        else:
            run = 0
        previous = day

    current = 0
    cursor = date.today()
    if values.get(cursor.isoformat(), 0) == 0:
        cursor -= timedelta(days=1)

    while values.get(cursor.isoformat(), 0) > 0:
        current += 1
        cursor -= timedelta(days=1)

    return current, longest

query = '''
query($login: String!) {
  user(login: $login) {
    login
    name
    followers { totalCount }
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false) {
      totalCount
      nodes { name stargazerCount }
    }
    contributionsCollection {
      totalCommitContributions
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
    }
  }
}
'''

user = graphql(query, {"login": USERNAME})["user"]
repos_count = int(user["repositories"]["totalCount"])
followers = int(user["followers"]["totalCount"])
stars = sum(int(r["stargazerCount"]) for r in user["repositories"]["nodes"])

collection = user["contributionsCollection"]
calendar = collection["contributionCalendar"]
days = [d for w in calendar["weeks"] for d in w["contributionDays"]]
contributions = int(calendar["totalContributions"])
commits = int(collection["totalCommitContributions"])
current_streak, longest_streak = streaks(days)

# Aggregate languages from owned, non-fork repositories.
language_sizes = {}
page = 1
while True:
    r = requests.get(
        f"https://api.github.com/users/{USERNAME}/repos",
        headers=HEADERS,
        params={"per_page": 100, "page": page, "type": "owner", "sort": "updated"},
        timeout=30,
    )
    r.raise_for_status()
    batch = r.json()
    if not batch:
        break
    for repo in batch:
        if repo.get("fork"):
            continue
        lr = requests.get(repo["languages_url"], headers=HEADERS, timeout=30)
        if lr.status_code != 200:
            continue
        for language, size in lr.json().items():
            language_sizes[language] = language_sizes.get(language, 0) + int(size)
    if len(batch) < 100:
        break
    page += 1

top_languages = sorted(language_sizes.items(), key=lambda x: x[1], reverse=True)[:6]
total_bytes = sum(language_sizes.values()) or 1

language_colors = {
    "Python": "#3776AB", "JavaScript": "#F7DF1E", "HTML": "#E34F26",
    "CSS": "#1572B6", "Java": "#ED8B00", "C": "#A8B9CC",
    "C++": "#00599C", "TypeScript": "#3178C6", "SQL": "#336791",
}

W, H = 1100, 1260
svg = [f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0%" stop-color="#020b18"/>
    <stop offset="100%" stop-color="#061a2d"/>
  </linearGradient>
  <linearGradient id="cyan" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0%" stop-color="#22d3ee"/>
    <stop offset="100%" stop-color="#38bdf8"/>
  </linearGradient>
</defs>
<rect width="{W}" height="{H}" rx="28" fill="url(#bg)"/>
<style>
.title {{font:700 31px Arial,sans-serif;fill:#f8fafc}}
.sub {{font:400 17px Arial,sans-serif;fill:#cbd5e1}}
.h2 {{font:700 20px Arial,sans-serif;fill:#e2e8f0}}
.label {{font:400 13px Arial,sans-serif;fill:#94a3b8}}
.value {{font:700 24px Arial,sans-serif;fill:#f8fafc}}
.small {{font:400 12px Arial,sans-serif;fill:#cbd5e1}}
.card {{fill:#031426;stroke:#164e70;stroke-width:1.2}}
</style>
''']

# Header
svg += [
    '<circle cx="82" cy="83" r="50" fill="#071d31" stroke="url(#cyan)" stroke-width="5"/>',
    '<text x="82" y="95" text-anchor="middle" font-family="Arial" font-size="30" font-weight="700" fill="#67e8f9">RY</text>',
    '<text x="155" y="70" class="title">👋 Hi, I&apos;m Rohit Yadav</text>',
    '<text x="155" y="101" class="sub">BCA Student  |  Aspiring Web Developer  |  Tech Enthusiast</text>',
    '<text x="155" y="130" class="small">Building projects • Learning new technologies • Creating a better tomorrow</text>',
    f'<text x="1020" y="73" text-anchor="end" class="small">Followers</text><text x="1020" y="100" text-anchor="end" class="value">{followers}</text>',
    f'<text x="1020" y="125" text-anchor="end" class="small">⭐ Stars</text><text x="1020" y="151" text-anchor="end" class="value">{stars}</text>',
]

def section(y, title):
    svg.append(f'<text x="40" y="{y}" class="h2">{title}</text>')
    svg.append(f'<line x1="40" y1="{y+12}" x2="1060" y2="{y+12}" stroke="#123b58"/>')

section(188, "📊 GitHub Overview")

cards = [
    ("🔥", "Current Streak", f"{current_streak} days"),
    ("🏆", "Longest Streak", f"{longest_streak} days"),
    ("💻", "Commits (1Y)", compact(commits)),
    ("🟩", "Contributions (1Y)", compact(contributions)),
    ("📦", "Repositories", compact(repos_count)),
]
for x, (icon, label, value) in zip([40, 250, 460, 670, 880], cards):
    svg += [
        f'<rect x="{x}" y="220" width="190" height="105" rx="16" class="card"/>',
        f'<text x="{x+18}" y="249" font-size="20">{icon}</text>',
        f'<text x="{x+18}" y="274" class="label">{esc(label)}</text>',
        f'<text x="{x+18}" y="307" class="value">{esc(value)}</text>',
    ]

section(370, "🟩 Contribution Activity")
start_x, start_y, cell, gap = 48, 410, 12, 5
weeks = calendar["weeks"][-52:]
all_counts = [int(d["contributionCount"]) for d in days]
max_count = max(all_counts + [1])
fills = ["#0b2233", "#064e3b", "#087f5b", "#0fbf70", "#22e6a2"]

for col, week in enumerate(weeks):
    for row, d in enumerate(week["contributionDays"]):
        count = int(d["contributionCount"])
        level = 0 if count == 0 else min(4, 1 + int((count / max_count) * 3.99))
        x = start_x + col * (cell + gap)
        y = start_y + row * (cell + gap)
        svg.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="3" fill="{fills[level]}"/>')

svg += [
    '<text x="48" y="530" class="small">Less</text>',
]
for i, color in enumerate(fills):
    svg.append(f'<rect x="{86+i*18}" y="520" width="12" height="12" rx="3" fill="{color}"/>')
svg.append('<text x="188" y="530" class="small">More</text>')

section(585, "💻 Coding Activity")

svg += [
    '<rect x="40" y="615" width="500" height="245" rx="18" class="card"/>',
    '<text x="62" y="650" class="h2">📚 Most Used Languages</text>',
]

cx, cy, radius, inner = 155, 750, 72, 42
circ = 2 * math.pi * radius
offset = 0
for idx, (lang, size) in enumerate(top_languages):
    pct = size / total_bytes
    dash = pct * circ
    color = language_colors.get(lang, ["#38bdf8","#a78bfa","#f472b6","#facc15","#34d399","#fb7185"][idx % 6])
    svg.append(
        f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="none" stroke="{color}" '
        f'stroke-width="28" stroke-dasharray="{dash:.2f} {circ-dash:.2f}" '
        f'stroke-dashoffset="{-offset:.2f}" transform="rotate(-90 {cx} {cy})"/>'
    )
    offset += dash

svg += [
    f'<circle cx="{cx}" cy="{cy}" r="{inner}" fill="#031426"/>',
    f'<text x="{cx}" y="{cy-3}" text-anchor="middle" class="small">Top</text>',
    f'<text x="{cx}" y="{cy+14}" text-anchor="middle" class="small">Languages</text>',
]

for i, (lang, size) in enumerate(top_languages):
    pct = size / total_bytes * 100
    y = 682 + i * 26
    color = language_colors.get(lang, "#38bdf8")
    svg += [
        f'<circle cx="258" cy="{y-5}" r="6" fill="{color}"/>',
        f'<text x="272" y="{y}" class="small">{esc(lang)}</text>',
        f'<text x="470" y="{y}" text-anchor="end" class="small">{pct:.1f}%</text>',
    ]

svg += [
    '<rect x="560" y="615" width="500" height="245" rx="18" class="card"/>',
    '<text x="582" y="650" class="h2">🔥 Coding Streak</text>',
    '<text x="582" y="690" class="label">Current Streak</text>',
    f'<text x="582" y="725" class="value">{current_streak} days</text>',
    '<line x1="805" y1="672" x2="805" y2="750" stroke="#164e70"/>',
    '<text x="830" y="690" class="label">Longest Streak</text>',
    f'<text x="830" y="725" class="value">{longest_streak} days</text>',
    '<rect x="582" y="770" width="435" height="45" rx="10" fill="#053b3a"/>',
    '<text x="602" y="798" class="small">Live GitHub activity — updated automatically.</text>',
]

section(900, "🧑‍💻 Developer Profile")
profiles = [
    ("🐍", "Python", "Django • FastAPI • Pandas"),
    ("🌐", "Web Development", "HTML • CSS • JavaScript • Bootstrap"),
    ("☕", "Programming", "Java • C • Data Structures"),
    ("🗄️", "Database", "PostgreSQL • SQLite • SQL"),
]
for i, (icon, title, body) in enumerate(profiles):
    x = 40 + i * 255
    svg += [
        f'<rect x="{x}" y="930" width="235" height="105" rx="16" class="card"/>',
        f'<text x="{x+18}" y="961" font-size="20">{icon}</text>',
        f'<text x="{x+52}" y="961" class="h2" font-size="17">{esc(title)}</text>',
        f'<text x="{x+18}" y="990" class="small">{esc(body)}</text>',
    ]

section(1070, "🛠️ Live GitHub Metrics")
metrics = [
    f"Contributions: {compact(contributions)}",
    f"Commits: {compact(commits)}",
    f"Repositories: {compact(repos_count)}",
    f"Followers: {compact(followers)}",
    f"Stars: {compact(stars)}",
]
for i, text in enumerate(metrics):
    svg.append(f'<text x="{45+i*205}" y="1110" class="small">{esc(text)}</text>')

svg += [
    '<text x="550" y="1165" text-anchor="middle" class="small">Updated automatically by GitHub Actions • Live data from GitHub API</text>',
    '<text x="550" y="1200" text-anchor="middle" class="small">Code → Learn → Build → Improve → Repeat 🚀</text>',
    '</svg>',
]

Path("github-overview.svg").write_text("\n".join(svg), encoding="utf-8")
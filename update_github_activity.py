import os
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from collections import defaultdict
from xml.sax.saxutils import escape


USERNAME = "diwakarchaudhary07"

API = "https://api.github.com"

TOKEN = os.environ.get("GITHUB_TOKEN")

HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2026-03-10",
    "User-Agent": USERNAME
}

if TOKEN:
    HEADERS["Authorization"] = f"Bearer {TOKEN}"


def github_get(url):

    request = urllib.request.Request(
        url,
        headers=HEADERS
    )

    with urllib.request.urlopen(
        request,
        timeout=30
    ) as response:

        return response.read().decode("utf-8")


def get_json(url):

    import json

    return json.loads(
        github_get(url)
    )


# -----------------------------
# GET REPOSITORIES
# -----------------------------

def get_repositories():

    repositories = []

    page = 1

    while True:

        params = urllib.parse.urlencode({
            "per_page": 100,
            "page": page,
            "type": "owner",
            "sort": "updated"
        })

        url = (
            f"{API}/users/"
            f"{USERNAME}/repos?"
            f"{params}"
        )

        data = get_json(url)

        if not data:
            break

        repositories.extend(data)

        if len(data) < 100:
            break

        page += 1

    return repositories


# -----------------------------
# GET COMMITS
# -----------------------------

def get_commits(repo, since):

    owner = repo["owner"]["login"]

    name = repo["name"]

    commits = []

    page = 1

    while True:

        params = urllib.parse.urlencode({
            "since": since.isoformat()
                .replace("+00:00", "Z"),
            "per_page": 100,
            "page": page
        })

        url = (
            f"{API}/repos/"
            f"{owner}/{name}/commits?"
            f"{params}"
        )

        try:

            data = get_json(url)

        except Exception:

            break

        if not data:
            break

        commits.extend(data)

        if len(data) < 100:
            break

        page += 1

    return commits


# -----------------------------
# DATE
# -----------------------------

india = ZoneInfo("Asia/Kolkata")

now = datetime.now(india)

start_date = now - timedelta(
    days=365
)


# -----------------------------
# STATISTICS
# -----------------------------

monthly = defaultdict(int)

weekday = defaultdict(int)

repositories = defaultdict(int)

month_order = []

cursor = datetime(
    start_date.year,
    start_date.month,
    1,
    tzinfo=india
)

while cursor <= now:

    month_order.append(
        cursor.strftime("%b")
    )

    if cursor.month == 12:

        cursor = datetime(
            cursor.year + 1,
            1,
            1,
            tzinfo=india
        )

    else:

        cursor = datetime(
            cursor.year,
            cursor.month + 1,
            1,
            tzinfo=india
        )


# -----------------------------
# PROCESS
# -----------------------------

print(
    f"Updating activity for {USERNAME}"
)

repo_list = get_repositories()

print(
    f"Found {len(repo_list)} repositories"
)


for repo in repo_list:

    repo_name = repo["name"]

    print(
        f"Processing {repo_name}"
    )

    commits = get_commits(
        repo,
        start_date
    )

    for commit in commits:

        commit_info = commit.get(
            "commit",
            {}
        )

        author = commit_info.get(
            "author"
        )

        if not author:
            continue

        date_string = author.get(
            "date"
        )

        if not date_string:
            continue

        try:

            commit_date = datetime.fromisoformat(
                date_string.replace(
                    "Z",
                    "+00:00"
                )
            ).astimezone(india)

        except Exception:

            continue

        if commit_date < start_date:
            continue

        # Month
        monthly[
            commit_date.strftime("%b")
        ] += 1

        # Weekday
        weekday[
            commit_date.strftime("%a")
        ] += 1

        # Repository
        repositories[
            repo_name
        ] += 1


# -----------------------------
# SVG TEXT
# -----------------------------

def text(
    x,
    y,
    value,
    size=14,
    weight="normal",
    color="#dbe7f5"
):

    return (
        f'<text x="{x}" y="{y}" '
        f'fill="{color}" '
        f'font-size="{size}" '
        f'font-family="Arial" '
        f'font-weight="{weight}">'
        f'{escape(str(value))}'
        f'</text>'
    )


# -----------------------------
# REPOSITORY ACTIVITY SVG
# -----------------------------

def create_repository_svg():

    months = [
        monthly[m]
        for m in month_order
    ]

    maximum = max(months) if months else 1

    if maximum < 10:
        maximum = 10

    svg = []

    svg.append(
        '<svg width="700" height="390" '
        'viewBox="0 0 700 390" '
        'xmlns="http://www.w3.org/2000/svg">'
    )

    svg.append(
        '<rect width="700" height="390" '
        'rx="14" '
        'fill="#061526" '
        'stroke="#23496d" '
        'stroke-width="2"/>'
    )

    svg.append(
        text(
            40,
            52,
            "Repository Activity",
            25,
            "bold",
            "#f5f7fa"
        )
    )

    svg.append(
        text(
            575,
            52,
            "● Commits",
            15,
            "normal",
            "#9fb8d6"
        )
    )

    # GRID

    for i in range(5):

        y = 95 + i * 50

        svg.append(
            f'<line x1="70" y1="{y}" '
            f'x2="660" y2="{y}" '
            f'stroke="#23496d"/>'
        )

    # Y labels

    for i in range(5):

        value = round(
            maximum -
            (maximum / 4) * i
        )

        y = 100 + i * 50

        svg.append(
            text(
                38,
                y,
                value,
                13
            )
        )

    # BARS

    spacing = 590 / max(
        len(months),
        1
    )

    for i, value in enumerate(months):

        bar_width = 27

        x = (
            70 +
            i * spacing +
            (spacing - bar_width) / 2
        )

        height = (
            value / maximum
        ) * 200

        y = 295 - height

        svg.append(
            f'<rect x="{x:.1f}" '
            f'y="{y:.1f}" '
            f'width="{bar_width}" '
            f'height="{height:.1f}" '
            f'rx="3" '
            f'fill="#4d7cff"/>'
        )

        svg.append(
            text(
                x + 5,
                y - 7,
                value,
                12,
                "bold",
                "#f5f7fa"
            )
        )

        svg.append(
            text(
                x,
                325,
                month_order[i],
                13
            )
        )

    svg.append("</svg>")

    with open(
        "repository-activity.svg",
        "w",
        encoding="utf-8"
    ) as file:

        file.write(
            "\n".join(svg)
        )


# -----------------------------
# DAY OF WEEK SVG
# -----------------------------

def create_weekday_svg():

    days = [
        "Mon",
        "Tue",
        "Wed",
        "Thu",
        "Fri",
        "Sat",
        "Sun"
    ]

    values = [
        weekday[d]
        for d in days
    ]

    maximum = max(values) if values else 1

    if maximum < 10:
        maximum = 10

    svg = []

    svg.append(
        '<svg width="700" height="390" '
        'viewBox="0 0 700 390" '
        'xmlns="http://www.w3.org/2000/svg">'
    )

    svg.append(
        '<rect width="700" height="390" '
        'rx="14" '
        'fill="#061526" '
        'stroke="#23496d" '
        'stroke-width="2"/>'
    )

    svg.append(
        text(
            40,
            52,
            "Activity by Day of Week",
            25,
            "bold",
            "#f5f7fa"
        )
    )

    # GRID

    for i in range(5):

        y = 95 + i * 50

        svg.append(
            f'<line x1="70" y1="{y}" '
            f'x2="660" y2="{y}" '
            f'stroke="#23496d"/>'
        )

    # Y LABELS

    for i in range(5):

        value = round(
            maximum -
            (maximum / 4) * i
        )

        y = 100 + i * 50

        svg.append(
            text(
                35,
                y,
                value,
                13
            )
        )

    colors = [
        "#287cff",
        "#21d18b",
        "#7747e8",
        "#ff9d32",
        "#f04b5d",
        "#19bce8",
        "#e843a8"
    ]

    spacing = 590 / 7

    for i, value in enumerate(values):

        width = 55

        x = (
            70 +
            i * spacing +
            (spacing - width) / 2
        )

        height = (
            value / maximum
        ) * 200

        y = 295 - height

        svg.append(
            f'<rect x="{x:.1f}" '
            f'y="{y:.1f}" '
            f'width="{width}" '
            f'height="{height:.1f}" '
            f'rx="4" '
            f'fill="{colors[i]}"/>'
        )

        svg.append(
            text(
                x + 18,
                y - 10,
                value,
                14,
                "bold",
                "#f5f7fa"
            )
        )

        svg.append(
            text(
                x + 12,
                325,
                days[i],
                14
            )
        )

    svg.append("</svg>")

    with open(
        "activity-by-day.svg",
        "w",
        encoding="utf-8"
    ) as file:

        file.write(
            "\n".join(svg)
        )


# -----------------------------
# GENERATE
# -----------------------------

create_repository_svg()

create_weekday_svg()

print("Activity SVGs generated successfully!")

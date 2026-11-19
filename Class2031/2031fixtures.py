import re, json
from datetime import datetime, date
import requests
from bs4 import BeautifulSoup

URL = "https://southwalesbasketball.leaguerepublic.com/team/453307591/796295714.html"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "en-GB,en;q=0.9",
}
TEAM = "Leadonites BC U14"

DATE_RE = re.compile(r"(\d{1,2}/\d{1,2}/\d{2,4})")
TIME_RE = re.compile(r"\b(\d{1,2}:\d{2})\b")
SCORE_RE = re.compile(r"(\d+)\s*-\s*(\d+)")


def isUs(name):
    return TEAM.lower() in name.lower()


def parseRows():
    r = requests.get(URL, timeout=15, headers=HEADERS)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    rows = []
    for tr in soup.select("table tr"):
        cells = [td.get_text(" ", strip=True) for td in tr.find_all("td")]
        if len(cells) < 5:
            continue  # header / standings / layout rows

        date_m = DATE_RE.search(cells[1])
        if not date_m:
            continue

        fmt = "%d/%m/%Y" if len(date_m[1].split("/")[-1]) == 4 else "%d/%m/%y"
        time_m = TIME_RE.search(cells[1])

        rows.append({
            "date": datetime.strptime(date_m[1], fmt).date(),
            "time": time_m[1] if time_m else "",
            "home": cells[2],
            "away": cells[4],
            "result": cells[3],
        })
    return [r for r in rows if isUs(r["home"]) or isUs(r["away"])]


def scrapeResults(rows, limit=3):
    results = []
    for row in rows:
        m = SCORE_RE.search(row["result"])
        if not m:
            continue  # unplayed
        results.append({
            "date": row["date"].isoformat(),
            "home": row["home"],
            "away": row["away"],
            "homeScore": int(m[1]),
            "awayScore": int(m[2]),
            "opponent": row["away"] if isUs(row["home"]) else row["home"],
        })
    results.sort(key=lambda x: x["date"], reverse=True)  # newest first
    return results[:limit]


def scrapeFixtures(rows, limit=3):
    today, fixtures = date.today(), []
    for row in rows:
        if SCORE_RE.search(row["result"]):
            continue  # already played
        if row["date"] < today:
            continue  # stale/unrecorded past fixture
        fixtures.append({
            "date": row["date"].isoformat(),
            "time": row["time"],
            "home": row["home"],
            "away": row["away"],
            "opponent": row["away"] if isUs(row["home"]) else row["home"],
            "isHome": isUs(row["home"]),
        })
    fixtures.sort(key=lambda x: (x["date"], x["time"]))  # soonest first
    return fixtures[:limit]


if __name__ == "__main__":
    rows = parseRows()

    with open(f"Class2031/u14Results.json", "w", encoding="utf-8") as f:
        json.dump(scrapeResults(rows), f, indent=2)
    with open(f"Class2031/u14Fixtures.json", "w", encoding="utf-8") as f:
        json.dump(scrapeFixtures(rows), f, indent=2)
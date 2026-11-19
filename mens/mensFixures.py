import re, json
from datetime import datetime, date
import requests
from bs4 import BeautifulSoup

URL = "https://www.gbba.org.uk/allfixtures.asp?teamID=270&sID=107&wsID=18&cid=8"
TEAM = "Leadonites"

def parseRows():
    r = requests.get(URL, timeout=15, headers={"User-Agent": "Leadonites-fixtures-bot/1.0"})
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    rows, month_year = [], None
    for tr in soup.select("table tr"):
        cells = [td.get_text(" ", strip=True) for td in tr.find_all("td")]
        if not cells:
            continue

        # Month header rows, e.g. "November 2026", have nothing else filled in
        if re.fullmatch(r"[A-Za-z]+ \d{4}", cells[0]) and not any(cells[1:]):
            month_year = cells[0]
            continue

        if len(cells) < 6 or not month_year:
            continue

        day_m = re.match(r"(\d{1,2})", cells[0])
        if not day_m:
            continue

        rows.append({
            "date": datetime.strptime(f"{day_m[1]} {month_year}", "%d %B %Y").date(),
            "time": cells[1],
            "home": cells[3],
            "away": cells[5],
            "result": cells[4],
        })
    return rows


def scrapeResults(limit=3):
    results = []
    for row in parseRows():
        score_m = re.search(r"(\d+)\s*-\s*(\d+)", row["result"])
        if not score_m:
            continue  # unplayed
        results.append({
            "date": row["date"].isoformat(),
            "home": row["home"],
            "away": row["away"],
            "homeScore": int(score_m[1]),
            "awayScore": int(score_m[2]),
            "opponent": row["away"] if row["home"] == TEAM else row["home"],
        })
    results.sort(key=lambda x: x["date"], reverse=True)  # newest first
    return results[:limit]


def scrapeFixtures(limit=3):
    today = date.today()
    fixtures = []
    for row in parseRows():
        if re.search(r"\d+\s*-\s*\d+", row["result"]):
            continue  # already played
        if row["date"] < today:
            continue  # stale/unrecorded past fixture
        fixtures.append({
            "date": row["date"].isoformat(),
            "time": row["time"],
            "home": row["home"],
            "away": row["away"],
            "opponent": row["away"] if row["home"] == TEAM else row["home"],
            "isHome": row["home"] == TEAM,
        })
    fixtures.sort(key=lambda x: (x["date"], x["time"]))  # soonest first
    return fixtures[:limit]

if __name__ == "__main__":
    with open("mens/MensResults.json", "w") as f:
        json.dump(scrapeResults(), f, indent=2)
    with open("mens/MensFixtures.json", "w") as f:
        json.dump(scrapeFixtures(),f, indent=2)
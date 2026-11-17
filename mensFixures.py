import re, json
from datetime import datetime
import requests
from bs4 import BeautifulSoup

URL = "https://www.gbba.org.uk/allfixtures.asp?teamID=270&sID=107&wsID=18&cid=8"
TEAM = "Leadonites"

def scrape(limit=3):
    r = requests.get(URL, timeout=15, headers={"User-Agent": "Leadonites-fixtures-bot/1.0"})
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    results, month_year = [], None
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
        score_m = re.search(r"(\d+)\s*-\s*(\d+)", cells[4])
        if not (day_m and score_m):
            continue  # skips unplayed fixtures (empty result)

        home, away = cells[3], cells[5]
        hs, as_ = int(score_m[1]), int(score_m[2])
        date = datetime.strptime(f"{day_m[1]} {month_year}", "%d %B %Y").date()

        us_home = home == TEAM
        us, them = (hs, as_) if us_home else (as_, hs)
        results.append({
            "date": date.isoformat(),
            "home": home, 
            "away": away,
            "homeScore": hs, 
            "awayScore": as_,
            "opponent": away if us_home else home,
        })

    results.sort(key=lambda x: x["date"], reverse=True)
    return results[:limit]

if __name__ == "__main__":
    with open("MensResults.json", "w") as f:
        json.dump(scrape(), f, indent=2)
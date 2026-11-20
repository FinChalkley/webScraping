from bs4 import BeautifulSoup
import requests, json

url = "https://southwalesbasketball.leaguerepublic.com/fg/1_584610458.html"
headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "en-GB,en;q=0.9",
}

response = requests.get(url, headers=headers, timeout=15)
print(response.status_code)
response.raise_for_status()

# Save what we actually received so you can compare it with the browser
with open("Class2027/raw_page.html", "w", encoding="utf-8") as f:
    f.write(response.text)

soup = BeautifulSoup(response.text, "html.parser")
tables = soup.find_all("table")
print(f"{len(tables)} tables found")


def to_int(text):
    try:
        return int(text.replace("+", "").strip())
    except ValueError:
        return text


rows = []
for i, table in enumerate(tables):
    first_row = table.find("tr")
    #print(i, [c.get_text(strip=True) for c in first_row.find_all(["th", "td"])][:12] if first_row else None)

    candidate = []
    for tr in table.find_all("tr"):
        cells = [td.get_text(" ", strip=True) for td in tr.find_all("td")]
        # standings row: position, team, then 7 numeric columns
        if len(cells) >= 9 and cells[0].isdigit():
            pos, team, played, won, lost, pts_for, pts_against, diff, points = cells[:9]
            candidate.append({
                "position": int(pos),
                "team": team,
                "played": to_int(played),
                "won": to_int(won),
                "lost": to_int(lost),
                "for": to_int(pts_for),
                "against": to_int(pts_against),
                "difference": to_int(diff),
                "points": to_int(points),
            })
    if candidate:
        rows = candidate
        break

if not rows:
    raise SystemExit("No standings rows found - check raw_page.html (see notes)")

with open("Class2031/u14Table.json", "w", encoding="utf-8") as f:
    json.dump(rows, f, indent=2)

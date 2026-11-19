from bs4 import BeautifulSoup
import requests, json

URL = "https://www.gbba.org.uk/leaguetables.asp"
responce = requests.get(URL)
print(responce.status_code)

soup = BeautifulSoup(responce.text, "html.parser")

division = "Division 2"

#json file
rows = []
for table in soup.find_all("table"):
    if table.find("table") or division not in table.get_text():
        continue
    for tr in table.find_all("tr"):
        cells = [td.get_text(strip=True) for td in tr.find_all("td")]
        if cells and cells[0].isdigit():
            pos, team, played, won, lost, pts_for, pts_against, diff, points = cells[0:9]
            rows.append({
                "position": int(pos), "team": team, "played": int(played),
                "won": int(won), "lost": int(lost), "for": int(pts_for),
                "against": int(pts_against), "difference": int(diff),
                "points": points,
            })

if not rows:
    raise SystemExit("No rows found - page layout may have changed")

with open("mens/division2.json", "w") as f:
    json.dump(rows, f, indent=2)
from bs4 import BeautifulSoup
import requests, csv, json

url = "https://www.gbba.org.uk/leaguetables.asp"
responce = requests.get(url)
print(responce.status_code)

soup = BeautifulSoup(responce.text, "html.parser")

division = "Division 2"

#csv file
with open("table.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["Title", "price"])
    for table in soup.find_all("table"):
        if table.find("table") or division not in table.get_text():
            continue

        for tr in table.find_all("tr"):
            cells = [td.get_text(strip=True) for td in tr.find_all("td")]
            if cells and cells[0].isdigit():
                position, team, played, won, lost, pts_for, pts_against, diff, points = cells[0:9]
                writer.writerow([position, team, played, won, lost, pts_for, pts_against, diff, points])
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

with open("division2.json", "w") as f:
    json.dump(rows, f, indent=2)
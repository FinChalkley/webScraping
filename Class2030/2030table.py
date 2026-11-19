from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import json
import re

URL = "https://www.playhq.com/uk/basketball-england/org/your-basketball-league-cic/202627/15-or-group-1/e0161b3d/ladder"

options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")
options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

print("Loading page...")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
driver.get(URL)

# Wait for the stats rows rather than sleeping a fixed time
try:
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "tr[data-testid^='standing-']"))
    )
except Exception:
    print("Warning: standings rows didn't appear within timeout.")

html = driver.page_source
driver.quit()

soup = BeautifulSoup(html, "html.parser")

container = soup.find("div", {"data-testid": "ladder"})
if not container:
    raise SystemExit("Could not find the ladder container. Check the URL / page layout.")

# --- Right-hand table: P, PTS, %, W, L ---
stat_rows = container.find_all("tr", attrs={"data-testid": re.compile(r"^standing-\d+-data$")})
stat_rows.sort(key=lambda tr: int(re.search(r"standing-(\d+)-data", tr["data-testid"]).group(1)))

stats = []
for tr in stat_rows:
    cells = [td.get_text(strip=True) for td in tr.find_all("td")]
    if len(cells) >= 5:
        stats.append(cells[:5])

# --- Left-hand table: position + team name ---
teams = []
for tr in container.find_all("tr"):
    if tr.get("data-testid", "").startswith("standing-"):
        continue  # that's a stats row
    tds = tr.find_all("td")
    if len(tds) == 2 and tds[0].get_text(strip=True).isdigit():
        teams.append((int(tds[0].get_text(strip=True)), tds[1].get_text(strip=True)))

print(f"Found {len(teams)} team rows and {len(stats)} stat rows")

if not teams or not stats or len(teams) != len(stats):
    raise SystemExit("Team rows and stat rows don't line up - page layout may have changed or data didn't load.")

rows = []
for (pos, team), (p, pts, pct, w, l) in zip(teams, stats):
    rows.append({
        "position": pos,
        "team": team,
        "played": int(p),
        "won": int(w),
        "lost": int(l),
        "points": int(pts),
        "win_percentage": float(pct.replace(",", "")),
    })

with open("Class2030/2030table.json", "w") as f:
    json.dump(rows, f, indent=2)

print(f"Saved {len(rows)} rows")
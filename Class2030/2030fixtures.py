from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import json
import re
import time

URL = "https://www.playhq.com/uk/basketball-england/org/leadonites-basketball/e539e17d/ybl-202627/teams/leadonites-u15-zonal/e1a487a5"
MY_TEAM = "Leadonites U15 Zonal"  # adjust to the exact name shown on PlayHQ

def get_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    return webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=options
    )

def scrape_fixtures_and_results():
    driver = get_driver()
    driver.get(URL)

    # Wait for the games list to appear
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located(
                (By.XPATH, "//div[contains(@data-testid,'game') or contains(@data-testid,'fixture') or contains(@data-testid,'result')]")
            )
        )
    except Exception:
        print("Warning: game cards didn't load within timeout, continuing anyway.")

    time.sleep(3)  # Give it a bit more time for any late-loading content

    # Try to click a "Show All" / "View All" button if present, so we get more than default view
    try:
        buttons = driver.find_elements(By.XPATH, "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'show all') or contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'view all')]")
        if buttons:
            buttons[0].click()
            time.sleep(2)
    except Exception:
        pass

    driver.quit()

    # --- Parse the HTML we grabbed ---
    # We re-open a driver only to get page_source in a clean way.
    # (Instead of quitting twice, we'll refactor slightly below.)

def scrape_team_games():
    driver = get_driver()
    driver.get(URL)

    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='games-on-date']"))
        )
    except Exception:
        print("Warning: games list didn't load within timeout.")

    for _ in range(3):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

    html = driver.page_source
    driver.quit()

    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")

    date_re = re.compile(r"(\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4})")
    time_re = re.compile(r"(\d{1,2}:\d{2}\s?(?:AM|PM))", re.IGNORECASE)

    results, upcoming, seen = [], [], set()

    for group in soup.select("[data-testid='games-on-date']"):
        # The heading ("Sunday, 18 October 2026") is the first date-like text in the group
        m = date_re.search(group.get_text(" ", strip=True))
        if not m:
            continue
        date_iso = parse_date(m.group(1))
        if not date_iso:
            continue

        for card in group.select("[role='listitem']"):
            # Team names come from the links to team pages, in display order (home, away)
            names = []
            for a in card.select("a[href*='/teams/']"):
                name = a.get_text(strip=True)
                if name and name not in names:
                    names.append(name)
            if len(names) < 2:
                continue
            home, away = names[0], names[1]
            opponent = away if MY_TEAM.lower() in home.lower() else home

            lines = [l.strip() for l in card.get_text("\n", strip=True).split("\n") if l.strip()]
            scores = [int(l) for l in lines if re.fullmatch(r"\d{1,3}", l)]

            t = time_re.search(card.get_text(" ", strip=True))
            game_time = t.group(1) if t else ""

            key = (date_iso, home, away, game_time)
            if key in seen:
                continue
            seen.add(key)

            if len(scores) >= 2:
                results.append({
                    "date": date_iso,
                    "home": home,
                    "away": away,
                    "homeScore": scores[0],
                    "awayScore": scores[1],
                    "opponent": opponent,
                })
            else:
                upcoming.append({
                    "date": date_iso,
                    "time": game_time,
                    "home": home,
                    "away": away,
                    "opponent": opponent,
                })

    results.sort(key=lambda x: x["date"], reverse=True)
    upcoming.sort(key=lambda x: x["date"])

    with open("Class2030/2030results.json", "w") as f:
        json.dump(results[:3], f, indent=2)
    with open("Class2030/2030fixtures.json", "w") as f:
        json.dump(upcoming[:3], f, indent=2)


def parse_date(raw):
    """Convert PlayHQ-style dates to YYYY-MM-DD."""
    import datetime
    raw = raw.strip()
    # Try ISO
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", raw)
    if m:
        return raw[:10]
    # Try "Sat 25 Oct 2026" or "25 Oct 2026"
    m = re.match(r"(?:\w+\s+)?(\d{1,2})\s+([A-Za-z]{3,9})\s+(\d{4})", raw)
    if m:
        try:
            dt = datetime.datetime.strptime(f"{m.group(1)} {m.group(2)} {m.group(3)}", "%d %b %Y")
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            try:
                dt = datetime.datetime.strptime(f"{m.group(1)} {m.group(2)} {m.group(3)}", "%d %B %Y")
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                pass
    # Try DD/MM/YYYY
    m = re.match(r"(\d{1,2})/(\d{1,2})/(\d{2,4})", raw)
    if m:
        d, mo, y = m.groups()
        y = f"20{y}" if len(y) == 2 else y
        return f"{y}-{int(mo):02d}-{int(d):02d}"
    return None

if __name__ == "__main__":
    scrape_team_games()
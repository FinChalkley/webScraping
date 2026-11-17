from bs4 import BeautifulSoup
import requests, csv

url = "https://books.toscrape.com"
responce = requests.get(url)

print(responce.status_code)

soup = BeautifulSoup(responce.text, "html.parser")
books = soup.find_all("article", class_="product_pod")

for book in books:
    title = book.h3.a["title"]
    price = book.find("p", class_="price_color").text
    print(f"{title} - {price}")

with open("books.csv", "w", newline="") as f: # "w" opens file in write mode which means it deletes whatever was in the file before hand
    writer = csv.writer(f)
    writer.writerow(["Title", "price"])
    for book in books:
        title = book.h3.a["title"]
        price = book.find("p", class_="price_color").text
        writer.writerow([title, price])




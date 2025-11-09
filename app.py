from flask import Flask, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
import os

DEPARTMENTS = {
    "ece": 0, "cse": 1, "eee": 2, "biot": 3, "chem": 4,
    "mech": 5, "mme": 6, "sos": 7, "shm": 8, "civil": 9
}

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0"})

def fetch(url):
    try:
        r = session.get(url, timeout=(4, 8), allow_redirects=True)
        r.raise_for_status()
        return r.text
    except:
        return None

def scrape_all():
    out = []
    phone_pattern = re.compile(r"\+\d{1,3}\s*\d{10}|\b\d{10}\b")
    email_pattern = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
    url_cleaner = re.compile(r"https?://\S+")

    remove_labels = [
        r"EXTERNAL\s*LINK\s*:?",
        r"PERSONAL\s*WEB\s*PAGE\s*:?"
    ]

    for dept, id_ in DEPARTMENTS.items():
        fac_url = f"https://nitandhra.ac.in/dept/{dept}/faculty"
        try:
            html = fetch(fac_url)
            if not html:
                continue
        except:
            continue

        soup = BeautifulSoup(html, "html.parser")
        cards = soup.find_all("div", class_="well")

        for card in cards:
            img = card.find("img")
            name_tag = card.find("h5", class_="media-heading")
            all_h5 = card.find_all("h5")
            if not img or not name_tag or not all_h5:
                continue

            image = img.get("src", "")
            name = name_tag.get_text(strip=True)
            title = all_h5[-1].get_text(strip=True)

            entry = {
                "id": id_,
                "department": dept,
                "name": name,
                "title": title,
                "image": image,
                "email": None,
                "areas_of_interest": None,
                "number": None
            }

            link = card.find("a")
            if link and link.get("href"):
                full = urljoin(fac_url, link["href"])
                try:
                    sub_html = fetch(full)
                    if sub_html:
                        sub = BeautifulSoup(sub_html, "html.parser")
                        text = sub.get_text(" ", strip=True)

                        phone_match = phone_pattern.findall(text)
                        if phone_match:
                            entry["number"] = phone_match[0].strip()

                        email_match = email_pattern.findall(text)
                        if email_match:
                            entry["email"] = email_match[0].strip()

                        aoi_block = sub.find("b", string=lambda x: x and "AREAS OF INTEREST" in x.upper())
                        if aoi_block:
                            aoi_text = aoi_block.parent.get_text(" ", strip=True)
                            aoi_text = aoi_text.replace(aoi_block.get_text(strip=True), "")
                            aoi_text = aoi_text.strip(" :")
                            aoi_text = url_cleaner.sub("", aoi_text).strip()
                            
                            for pattern in remove_labels:
                                aoi_text = re.sub(pattern, "", aoi_text, flags=re.IGNORECASE)

                            aoi_text = aoi_text.strip()
                            entry["areas_of_interest"] = aoi_text if aoi_text else None
                except:
                    pass

            out.append(entry)

    out.sort(key=lambda x: (x["id"], x["name"].lower()))
    return out

app = Flask(__name__)
CORS(app)

# GET endpoint - returns scraped data
@app.get("/api/faculty")
def get_faculty():
    try:
        data = scrape_all()
        return jsonify({
            "status": "success",
            "data": data,
            "count": len(data)
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# Health check
@app.get("/")
def root():
    return jsonify({"status": "online", "message": "Faculty Scraper API"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=False)

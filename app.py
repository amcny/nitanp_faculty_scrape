from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
import os
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEPARTMENTS = {
    "ece": 0, "cse": 1, "eee": 2, "biot": 3, "chem": 4,
    "mech": 5, "mme": 6, "sos": 7, "shm": 8, "civil": 9
}

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0"})

# Global cache
cached_data = None
cache_timestamp = None
last_refresh = None

def fetch(url, timeout=(2, 3)):
    try:
        r = session.get(url, timeout=timeout, allow_redirects=False)
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
        logger.info(f"Scraping: {dept}")
        
        html = fetch(fac_url)
        if not html:
            continue

        try:
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
                        sub_html = fetch(full, timeout=(1, 2))
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

        except Exception as e:
            logger.error(f"Error in {dept}: {e}")

    out.sort(key=lambda x: (x["id"], x["name"].lower()))
    return out

app = Flask(__name__)
CORS(app)

# ROOT ENDPOINT
@app.get("/")
def root():
    return jsonify({
        "status": "online",
        "message": "NIT AP Faculty Scraper API",
        "endpoints": {
            "get_faculty": "/api/faculty",
            "refresh": "POST /api/faculty/refresh",
            "health": "/api/health"
        }
    }), 200

# Endpoint 1: Get cached data (FAST - no scraping)
@app.get("/api/faculty")
def get_faculty():
    global cached_data, cache_timestamp
    
    if not cached_data:
        return jsonify({
            "status": "no_data",
            "message": "No data cached. Click refresh first!",
            "data": []
        }), 200
    
    age = int(time.time() - cache_timestamp)
    return jsonify({
        "status": "success",
        "data": cached_data,
        "count": len(cached_data),
        "cached_age_seconds": age,
        "last_refresh": last_refresh
    }), 200

# Endpoint 2: Manually refresh (TRIGGERS SCRAPING)
@app.post("/api/faculty/refresh")
def refresh_faculty():
    global cached_data, cache_timestamp, last_refresh
    
    logger.info("MANUAL REFRESH TRIGGERED")
    
    try:
        # Do the scraping
        cached_data = scrape_all()
        cache_timestamp = time.time()
        last_refresh = time.strftime("%Y-%m-%d %H:%M:%S")
        
        logger.info(f"Refresh successful! {len(cached_data)} faculty")
        
        return jsonify({
            "status": "success",
            "message": f"Refreshed! Got {len(cached_data)} faculty",
            "data": cached_data,
            "count": len(cached_data),
            "last_refresh": last_refresh
        }), 200
    except Exception as e:
        logger.error(f"Refresh error: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# Endpoint 3: Health check
@app.get("/api/health")
def health():
    return jsonify({"status": "healthy"}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=False)

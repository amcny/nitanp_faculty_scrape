from flask import Flask, jsonify, send_file
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
import os
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

DEPARTMENTS = {
    "ece": 0, "cse": 1, "eee": 2, "biot": 3, "chem": 4,
    "mech": 5, "mme": 6, "sos": 7, "shm": 8, "civil": 9
}

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0"})

CACHE_FILE = "/tmp/faculty_cache.json"

def fetch(url, timeout=(3, 5)):
    try:
        r = session.get(url, timeout=timeout, allow_redirects=True)
        r.raise_for_status()
        return r.text
    except:
        return None

def scrape_department(dept, id_):
    """Scrape single department"""
    out = []
    phone_pattern = re.compile(r"\+\d{1,3}\s*\d{10}|\b\d{10}\b")
    email_pattern = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
    url_cleaner = re.compile(r"https?://\S+")
    remove_labels = [r"EXTERNAL\s*LINK\s*:?", r"PERSONAL\s*WEB\s*PAGE\s*:?"]

    fac_url = f"https://nitandhra.ac.in/dept/{dept}/faculty"
    
    html = fetch(fac_url)
    if not html:
        return out

    soup = BeautifulSoup(html, "html.parser")
    cards = soup.find_all("div", class_="well")

    for card in cards:
        img = card.find("img")
        name_tag = card.find("h5", class_="media-heading")
        all_h5 = card.find_all("h5")
        if not img or not name_tag or not all_h5:
            continue

        entry = {
            "id": id_,
            "department": dept,
            "name": name_tag.get_text(strip=True),
            "title": all_h5[-1].get_text(strip=True),
            "image": img.get("src", ""),
            "email": None,
            "areas_of_interest": None,
            "number": None
        }

        link = card.find("a")
        if link and link.get("href"):
            full = urljoin(fac_url, link["href"])
            try:
                sub_html = fetch(full, timeout=(2, 3))
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
                        entry["areas_of_interest"] = aoi_text.strip() if aoi_text.strip() else None
            except:
                pass

        out.append(entry)

    return out

def scrape_all():
    """Scrape all departments in parallel"""
    all_faculty = []
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(scrape_department, dept, id_): dept 
            for dept, id_ in DEPARTMENTS.items()
        }
        
        for future in as_completed(futures):
            try:
                faculty_list = future.result()
                all_faculty.extend(faculty_list)
            except Exception as e:
                print(f"Error: {e}")

    all_faculty.sort(key=lambda x: (x["id"], x["name"].lower()))
    return all_faculty

def save_cache(data):
    """Save scraped data to cache file"""
    try:
        with open(CACHE_FILE, 'w') as f:
            json.dump(data, f)
        print(f"Cache saved: {CACHE_FILE}")
    except Exception as e:
        print(f"Error saving cache: {e}")

def load_cache():
    """Load data from cache file"""
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading cache: {e}")
    return []

app = Flask(__name__)
CORS(app)

@app.get("/")
def root():
    return jsonify({"status": "online", "message": "Faculty Scraper API"})

@app.get("/api/faculty")
def get_faculty():
    """Get faculty from cache"""
    try:
        cached_data = load_cache()
        if cached_data:
            return jsonify({
                "status": "success",
                "data": cached_data,
                "count": len(cached_data),
                "source": "cache"
            })
        else:
            return jsonify({
                "status": "no_data",
                "data": [],
                "message": "No cached data. Click refresh first!"
            })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.post("/api/faculty/refresh")
def refresh_faculty():
    """Refresh faculty data and save to cache"""
    try:
        print("Starting refresh...")
        data = scrape_all()
        save_cache(data)
        
        return jsonify({
            "status": "success",
            "data": data,
            "count": len(data),
            "message": f"Refreshed! Got {len(data)} faculty",
            "source": "live"
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.get("/api/health")
def health():
    return jsonify({"status": "healthy"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=False)

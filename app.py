from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import pytz
from google.cloud import storage
import os

app = Flask(__name__)
CORS(app)

DEPARTMENTS = {
    "ece": 0, "cse": 1, "eee": 2, "biot": 3, "chem": 4,
    "mech": 5, "mme": 6, "sos": 7, "shm": 8, "civil": 9
}

GCS_BUCKET = os.environ.get('GCS_BUCKET', 'faculty-cache-api')

def get_gcs_client():
    return storage.Client()

def save_cache(data, timestamp):
    """Save faculty data and timestamp to Google Cloud Storage"""
    try:
        client = get_gcs_client()
        bucket = client.bucket(GCS_BUCKET)
        blob = bucket.blob("faculty_cache.json")
        cache_data = {'faculty': data, 'timestamp': timestamp}
        blob.upload_from_string(json.dumps(cache_data))
        print(f"Cache saved successfully at {timestamp}")
    except Exception as e:
        print(f"Error saving cache: {e}")

def load_cache():
    """Load faculty data and timestamp from Google Cloud Storage"""
    try:
        client = get_gcs_client()
        bucket = client.bucket(GCS_BUCKET)
        blob = bucket.blob("faculty_cache.json")
        if blob.exists():
            cache_data = json.loads(blob.download_as_string())
            return cache_data.get('faculty', []), cache_data.get('timestamp', '')
        return [], ''
    except Exception as e:
        print(f"Error loading cache: {e}")
        return [], ''

def get_current_timestamp():
    """Get current timestamp in Indian Standard Time (IST)"""
    ist = pytz.timezone('Asia/Kolkata')
    return datetime.now(ist).strftime("%Y-%m-%d %H:%M:%S IST")

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0"})

def fetch(url, timeout=(4, 8)):
    """Fetch URL content with error handling"""
    try:
        r = session.get(url, timeout=timeout, allow_redirects=True)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def scrape_department(dept, id_):
    """Scrape faculty data from a specific department"""
    out = []
    phone_pattern = re.compile(r"\+\d{1,3}\s*\d{10}|\b\d{10}\b")
    email_pattern = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
    url_cleaner = re.compile(r"https?://\S+")
    remove_labels = [r"EXTERNAL\s*LINK\s*:?", r"PERSONAL\s*WEB\s*PAGE\s*:?"]
    
    fac_url = f"https://nitandhra.ac.in/dept/{dept}/faculty"
    html = fetch(fac_url)
    
    if not html:
        print(f"Failed to fetch {dept} department")
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
                    
                    # Extract phone number
                    phone_match = phone_pattern.findall(text)
                    if phone_match:
                        entry["number"] = phone_match[0].strip()
                    
                    # Extract email
                    email_match = email_pattern.findall(text)
                    if email_match:
                        entry["email"] = email_match[0].strip()
                    
                    # Extract areas of interest
                    aoi_block = sub.find("b", string=lambda x: x and "AREAS OF INTEREST" in x.upper())
                    if aoi_block:
                        aoi_text = aoi_block.parent.get_text(" ", strip=True)
                        aoi_text = aoi_text.replace(aoi_block.get_text(strip=True), "")
                        aoi_text = aoi_text.strip(" :")
                        aoi_text = url_cleaner.sub("", aoi_text).strip()
                        for pattern in remove_labels:
                            aoi_text = re.sub(pattern, "", aoi_text, flags=re.IGNORECASE)
                        entry["areas_of_interest"] = aoi_text.strip() if aoi_text.strip() else None
            except Exception as e:
                print(f"Error scraping faculty detail for {entry['name']}: {e}")
        
        out.append(entry)
    
    return out

def scrape_all():
    """Scrape faculty data from all departments using parallel execution"""
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
                print(f"Error in scrape_all: {e}")
    
    # Sort by department ID and name
    all_faculty.sort(key=lambda x: (x["id"], x["name"].lower()))
    return all_faculty

@app.get("/")
def root():
    """Health check endpoint"""
    return jsonify({
        "status": "online", 
        "message": "Faculty Scraper API - Google Cloud Run",
        "timestamp": get_current_timestamp()
    })

@app.get("/api/faculty")
def get_faculty():
    """Get cached faculty data"""
    faculty_data, cached_timestamp = load_cache()
    
    if faculty_data:
        return jsonify({
            "status": "success",
            "data": faculty_data,
            "count": len(faculty_data),
            "source": "cache",
            "last_refreshed": cached_timestamp if cached_timestamp else get_current_timestamp()
        })
    else:
        return jsonify({
            "status": "no_data",
            "data": [],
            "count": 0,
            "message": "No cached data. Click refresh first!",
            "source": "cache",
            "last_refreshed": ""
        })

@app.post("/api/faculty/refresh")
def refresh_faculty():
    """Scrape live data and update cache"""
    try:
        print("Starting faculty data refresh...")
        data = scrape_all()
        current_time = get_current_timestamp()
        save_cache(data, current_time)
        
        return jsonify({
            "status": "success",
            "data": data,
            "count": len(data),
            "source": "live",
            "last_refreshed": current_time
        })
    except Exception as e:
        print(f"Error in refresh_faculty: {e}")
        return jsonify({
            "status": "error",
            "data": [],
            "count": 0,
            "message": str(e),
            "last_refreshed": ""
        }), 500

@app.get("/api/health")
def health_check():
    """Detailed health check"""
    return jsonify({
        "status": "online",
        "service": "Faculty Scraper API",
        "region": "asia-south1",
        "timestamp": get_current_timestamp()
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

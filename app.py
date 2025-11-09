from flask import Flask, jsonify
from flask_cors import CORS
import threading
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re

app = Flask(__name__)
CORS(app)

cached_data = []
last_refresh = None
refresh_requested = False

# ---------------- SCRAPER (unchanged) ---------------
def scrape_all():
    # your full scraping code here
    pass

# -------------- BACKGROUND REFRESH THREAD ----------
def refresher():
    global cached_data, last_refresh, refresh_requested
    while True:
        if refresh_requested or not cached_data:
            try:
                data = scrape_all()
                cached_data = data
                last_refresh = time.strftime("%Y-%m-%d %H:%M:%S")
            except:
                pass
            refresh_requested = False
        time.sleep(30)   # small cycle, non-blocking

t = threading.Thread(target=refresher, daemon=True)
t.start()

# ---------------- API ENDPOINTS --------------------

@app.get("/api/faculty")
def get_data():
    return jsonify({
        "data": cached_data,
        "count": len(cached_data),
        "last_refresh": last_refresh
    })

@app.post("/api/faculty/refresh")
def manual():
    global refresh_requested
    refresh_requested = True
    return jsonify({"status": "queued"})

@app.get("/api/health")
def health():
    return jsonify({"ok": True})

# ----------------------------------------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)

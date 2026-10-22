from __future__ import annotations
import csv, io, ipaddress, json, socket
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
from flask import Flask, Response, jsonify, render_template, request
app = Flask(__name__)
ALLOWED_HOSTS = {"justdial.com", "www.justdial.com"}
MAX_RESULTS = 100

def validate_url(raw_url: str) -> str:
    parsed = urlparse(raw_url.strip())
    if parsed.scheme != "https" or parsed.hostname not in ALLOWED_HOSTS:
        raise ValueError("Use a public https://www.justdial.com/... listing URL.")
    for item in socket.getaddrinfo(parsed.hostname, None):
        ip = ipaddress.ip_address(item[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local:
            raise ValueError("That URL is not allowed.")
    return parsed.geturl()

def clean(value: str | None) -> str:
    return " ".join((value or "").split())

def as_text(element, selector: str) -> str:
    node = element.select_one(selector)
    return clean(node.get_text(" ", strip=True) if node else "")

def extract_json_ld(soup: BeautifulSoup) -> list[dict]:
    records = []
    for script in soup.select('script[type="application/ld+json"]'):
        try: value = json.loads(script.get_text())
        except json.JSONDecodeError: continue
        for item in value if isinstance(value, list) else [value]:
            if not isinstance(item, dict) or item.get("@type") not in {"Physician", "MedicalClinic", "LocalBusiness", "Hospital"}: continue
            address = item.get("address", {})
            if isinstance(address, dict): address = clean(" ".join(str(v) for v in address.values() if v))
            records.append({"name": clean(item.get("name")), "specialty": clean(item.get("medicalSpecialty")), "address": clean(str(address)), "city": clean(item.get("address", {}).get("addressLocality") if isinstance(item.get("address"), dict) else ""), "rating": clean(str(item.get("aggregateRating", {}).get("ratingValue", ""))), "reviews": clean(str(item.get("aggregateRating", {}).get("reviewCount", ""))), "website": clean(item.get("url"))})
    return records

def extract_cards(soup: BeautifulSoup, selectors: dict[str, str]) -> list[dict]:
    cards = soup.select(selectors["card"])[:MAX_RESULTS]
    return [{"name": as_text(c, selectors["name"]), "specialty": as_text(c, selectors["specialty"]), "address": as_text(c, selectors["address"]), "city": as_text(c, selectors["city"]), "rating": as_text(c, selectors["rating"]), "reviews": as_text(c, selectors["reviews"]), "website": ""} for c in cards]

@app.get("/")
def home(): return render_template("index.html")

@app.post("/extract")
def extract():
    payload = request.get_json(force=True)
    try:
        url = validate_url(payload.get("url", ""))
        selectors = {key: payload.get(key, default) for key, default in {"card": ".resultbox, .cntanr, [data-testid='listing']", "name": "h2, h3, .lng_cont_name", "specialty": ".category, .cont_sw, .store-details", "address": ".cont_sw, .address, .cont_fl_addr", "city": ".city", "rating": ".green-box, .rating", "reviews": ".rt_count, .review"}.items()}
        response = requests.get(url, timeout=20, headers={"User-Agent": "PublicListingResearch/1.0"}); response.raise_for_status()
        rows = [row for row in (extract_json_ld(BeautifulSoup(response.text, "html.parser")) or extract_cards(BeautifulSoup(response.text, "html.parser"), selectors)) if row["name"]]
        return jsonify({"rows": rows[:MAX_RESULTS], "count": len(rows[:MAX_RESULTS])})
    except (ValueError, requests.RequestException) as error: return jsonify({"error": str(error)}), 400

@app.post("/csv")
def csv_download():
    rows = request.get_json(force=True).get("rows", []); output = io.StringIO()
    fields = ["name", "specialty", "address", "city", "rating", "reviews", "website"]
    writer = csv.DictWriter(output, fieldnames=fields); writer.writeheader()
    writer.writerows({key: row.get(key, "") for key in fields} for row in rows)
    return Response(output.getvalue(), mimetype="text/csv", headers={"Content-Disposition": "attachment; filename=doctor-listings.csv"})

if __name__ == "__main__": app.run(debug=True, port=5000)
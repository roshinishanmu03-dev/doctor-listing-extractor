# Doctor Listing Extractor

1. Install Python dependencies: `python3 -m pip install -r requirements.txt`
2. Start it: `python3 app.py`
3. Open `http://127.0.0.1:5000` and paste one public Justdial listing URL.

The app accepts only `https://www.justdial.com/...` URLs, extracts up to 100 public records per page, previews them, and downloads a CSV. It does not collect hidden or click-to-reveal contact details. Before collecting at scale, confirm the site's terms, robots policy, and rate limits.
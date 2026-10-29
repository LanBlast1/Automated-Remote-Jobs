# Remote Jobs Pipeline

## Problem

Finding remote jobs across multiple boards is repetitive. This project automates collecting, storing, and reviewing job listings.

## Sources

- We Work Remotely
- RemoteOK API

## Pipeline

1. **Extract**: Fetch HTML and JSON data using `requests`.
2. **Parse**: Parse We Work Remotely HTML with BeautifulSoup and RemoteOK JSON with Python's `json` module.
3. **Normalize**: Extract title, company name, location, link, source, scraped timestamp, and tags.
4. **Load**: Store records in SQLite. Duplicate links are ignored using `UNIQUE(link)` and `INSERT OR IGNORE`.
5. **Serve**: View jobs in a Streamlit dashboard with a simple tag filter.

## Features

- Scrapes jobs from We Work Remotely and RemoteOK
- Deduplicates jobs by link
- Stores data in a local SQLite database
- Logs runs and errors to `pipeline.log`
- CLI menu for:
  - viewing newest jobs
  - marking jobs as applied
  - searching jobs
  - exporting a showcase database
- Streamlit dashboard with simple tag filtering

## Demo Data

This repository includes `showcase.db`, a sanitized snapshot of scraped job listings.

The dashboard uses:

- `jobs.db` locally if it exists
- `showcase.db` as the public demo database if `jobs.db` is not present

`showcase.db` does not contain the personal `applied_at` column.

## Tech Stack

- Python
- requests
- BeautifulSoup
- sqlite3
- pandas
- Streamlit

## How to Run

Clone the repository.

Install dependencies:

```bash
pip install requests beautifulsoup4 pandas streamlit
```

Run the scraper and CLI menu:
```bash
python main.py
```

Run the Streamlit dashboard:
```bash
streamlit run app.py
```

## Current Limitations
- Scraping is run manually
- Uses SQLite only
- Tags are stored as comma-separated text
- Tag filter is approximate substring matching
- No authentication
- No scheduled refresh

## Next Steps
- Improve tag filtering with normalized tags
- Schedule automatic scraping
- Add basic tests
- Move to PostgreSQL if needed

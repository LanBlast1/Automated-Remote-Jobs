# Automated Remote Jobs ETL Pipeline

This project extracts job listings from the website https://weworkremotely.com using `requests` and `beautifulsoup4` library in Python. Extracted data has been cleaned and stored in a database using `sqlite3` for easy access and to avoid loss of data.

## Architecture / Pipeline Flow
- Extract: For data extraction, custom user agent in headers were used to gain access to the website
- Transform: Data cleaning was done by handling None or missing values by assigning 'Unknown' to the missing feature 
- Load: For storing, `sqlite3` was used as it provides a sql database which avoids data depuplication
## Tech Stack
- Language: Python
- Libraries: requests, BeautifulSoup, sqlite3, logging
- Database: SQLite
## Key Engineering Features
- Implemented INSERT or IGNORE INTO so as to avoid any duplicate values being inserted into the database.
- Used logging to keep track of data collection and any current or future errors. 
## How to Run
- Clone the repository
- Install dependencies: `pip install requests beautifulsoup4`
- Run the pipeline: python scraper.py
- View the database: `sqlite3 jobs.db`
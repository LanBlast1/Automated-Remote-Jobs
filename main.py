import logging
import sqlite3
import requests
from bs4 import BeautifulSoup
from datetime import datetime as dt
from contextlib import closing
import json
import sys

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    style="%",
    filename="pipeline.log",
    level=logging.INFO
)


def fetch(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException as e:
        logging.warning("Error Occurred: %s for the website whose url is: %s", e,url)
        return None

def parse_html(content):
    if content == None:
        return None
    soup = BeautifulSoup(content, "html.parser")
    containers = soup.find_all("li", class_="new-listing-container")
    job_listings = []
    for container in containers:
        job_post = {}
        title = container.find("span", class_="new-listing__header__title__text")
        job_post["title"] = title.get_text(strip=True) if title else ""
        company_name = container.find("p", class_="new-listing__company-name")
        job_post["company_name"] = (
            company_name.get_text(strip=True) if company_name else None
        )
        location = container.find("p", class_="new-listing__company-headquarters")
        job_post["location"] = location.get_text(strip=True) if location else None
        link = container.find("a", class_="listing-link--unlocked")
        job_post["link"] = (
            "https://weworkremotely.com" + link.get("href").strip()
            if (link and link.get("href"))
            else None
        )
        job_post["source"] = "WeWorkRemotely"
        job_post["scraped_at"] = str(dt.now().isoformat())
        job_listings.append(job_post)
    return job_listings


def parse_json(content):
    json_data = json.loads(content)
    job_listings = []
    for job in json_data[1:]:
        job_post = {}
        title = job.get("position", "")
        job_post["title"] = title

        company_name = job.get("company", "")
        job_post["company_name"] = company_name

        location = job.get("location", "")
        job_post["location"] = location

        link = (job.get("url", "")).lower() if job.get("url", "") != "" else None
        job_post["link"] = link

        source = "remoteok"
        job_post["source"] = source

        scraped_at = str(dt.now().isoformat())
        job_post["scraped_at"] = scraped_at
        job_listings.append(job_post)
    return job_listings


def load(listings):
    length=len(listings)
    with closing(sqlite3.connect("jobs.db")) as con:
        cur = con.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS jobs(
                    title TEXT,
                    company_name TEXT,
                    location TEXT,
                    link  TEXT NOT NULL UNIQUE,
                     source TEXT,
                      scraped_at TEXT )""")
        cur.executemany(
            """INSERT OR IGNORE INTO
         jobs(title,company_name,location,link,source,scraped_at)
          VALUES(:title,:company_name,:location,:link,:source,:scraped_at) 
          """,
            listings,
        )
        rowcount= cur.rowcount
        delta=length-rowcount
        logging.info("Inserted %d out of %d,delta is %d",rowcount,length,delta)
        con.commit()
    return delta
def main():
    # We Work Remotely
    url1 = "https://weworkremotely.com/remote-jobs"
    content_wwr = fetch(url1)
    if content_wwr == None:
        logging.warning("No response.")
    job_listings_wwr = parse_html(content_wwr)
    if job_listings_wwr == []:
        logging.warning("Nothing was scraped.")
    rowcount_wwr = load(job_listings_wwr)

    # Remoteok
    url2 = "https://remoteok.com/api"
    content_ro = fetch(url2)
    if content_ro == None:
        logging.warning("No response.")
    job_listings_ro = parse_json(content_ro)
    if job_listings_ro == []:
        logging.warning("Nothing was scraped.")
    rowcount_ro = load(job_listings_ro)
    if rowcount_ro > 1:
        logging.warning("Duplicate entries were inserted with rowcount=%d", rowcount_ro)


if __name__ == "__main__":
    main()

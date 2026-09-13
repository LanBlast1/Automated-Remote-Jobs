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
    level=logging.INFO,
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
        logging.warning("Error Occurred: %s for the website whose url is: %s", e, url)
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
        job_post["title"] = title.get_text(strip=True) if title else None
        company_name = container.find("p", class_="new-listing__company-name")
        job_post["company_name"] = (
            company_name.get_text(strip=True) if company_name else None
        )
        location = container.find("p", class_="new-listing__company-headquarters")
        job_post["location"] = location.get_text(strip=True) if location else None
        link = container.find("a", class_="listing-link--unlocked")
        if link is None or link.get("href") is None:
            logging.warning("Skipping the job record %s as no link exists",title)
            continue
        job_post["link"] = "https://weworkremotely.com" + link.get("href").strip()
        job_post["source"] = "weworkremotely"
        job_post["scraped_at"] = str(dt.now().isoformat())
        job_listings.append(job_post)
    return job_listings


def parse_json(content):
    if content == None:
        return None
    json_data = json.loads(content)
    job_listings = []
    for job in json_data[1:]:
        job_post = {}
        title = job.get("position", None)
        job_post["title"] = title if title != "" else None

        company_name = job.get("company", None)
        job_post["company_name"] = company_name if company_name != "" else None

        location = job.get("location", None)
        job_post["location"] = location if location != "" else None

        link = job.get("url", None) if job.get("url", None) != "" else None
        if link is None:
            logging.warning("Skipping the job record %s as no link exists",title)
            continue
        job_post["link"] = link.lower() if link else None

        source = "remoteok"
        job_post["source"] = source

        scraped_at = str(dt.now().isoformat())
        job_post["scraped_at"] = scraped_at
        job_listings.append(job_post)
    return job_listings


def load(listings):
    length = len(listings)
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
        rowcount = cur.rowcount
        delta = length - rowcount
        logging.info("Inserted %d out of %d,delta is %d", rowcount, length, delta)
        con.commit()
    if rowcount == 0:
        logging.info("No new rows inserted into the database.")


def main(source,url,parser):
    logging.info(source+"-")
    content=fetch(url)
    if content is None:
        logging.warning("No response.")
        return None
    else:
        job_listings=parser(content)
        if not job_listings:
            logging.warning("Nothing was scraped")
            return None
        load(job_listings)


if __name__ == "__main__":
    url1="https://weworkremotely.invalid"
    url2="https://remoteok.com/api"    
    sources=[("weworkremotely",url1,parse_html),("remoteok",url2,parse_json)]
    for i in sources:
        main(i[0],i[1],i[2])

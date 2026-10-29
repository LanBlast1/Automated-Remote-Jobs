import os
import logging
import sqlite3
import requests
from bs4 import BeautifulSoup
from datetime import datetime as dt
from contextlib import closing
import json
from urllib.parse import urlsplit, urlunsplit
import sys

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    style="%",
    filename="pipeline.log",
    level=logging.INFO,
)

DB_PATH="jobs.db"


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
    if content is None:
        return []
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
            logging.warning(
                "Skipping %s record as no link exists",
                (title.get_text(strip=True) if title else None)
                or (company_name.get_text(strip=True) if company_name else None)
                or "Unknown",
            )
            continue
        job_post["link"] = "https://weworkremotely.com" + link.get("href").strip()
        job_post["source"] = "weworkremotely"
        job_post["scraped_at"] = str(dt.now().isoformat())
        job_post["tags"]=None
        job_listings.append(job_post)
    return job_listings


def parse_json(content):
    if content is None:
        return []
    try:
        json_data = json.loads(content)
    except json.JSONDecodeError:
        logging.warning("Response is not valid JSON, returning empty list")
        return []
    if not isinstance(json_data, list):
        logging.warning("Unexpected JSON shape, returning empty list")  
        return []
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
            logging.warning(
                "Skipping %s record as no link exists",
                title or company_name or "unknown record",
            )
            continue
        result = urlsplit(link)
        link_modify = result._replace(netloc=result.netloc.lower())
        new_link = urlunsplit(link_modify)
        job_post["link"] = new_link
        source = "remoteok"
        job_post["source"] = source

        scraped_at = str(dt.now().isoformat())
        job_post["scraped_at"] = scraped_at

        tags=job.get("tags") or None
        job_post["tags"]=",".join(tags) if tags else None
        job_listings.append(job_post)
    return job_listings


def load(listings,db_path=DB_PATH):
    length = len(listings)
    with closing(sqlite3.connect(db_path)) as con:
        cur = con.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS jobs(
                    title TEXT,
                    company_name TEXT,
                    location TEXT,
                    link  TEXT NOT NULL UNIQUE,
                     source TEXT,
                      scraped_at TEXT,
                       tags TEXT,
                        applied_at TEXT )""")
        cur.executemany(
            """INSERT OR IGNORE INTO
         jobs(title,company_name,location,link,source,scraped_at,tags)
          VALUES(:title,:company_name,:location,:link,:source,:scraped_at,:tags) 
          """,
            listings,
        )
        rowcount = cur.rowcount
        delta = length - rowcount
        logging.info("Inserted %d out of %d,delta is %d", rowcount, length, delta)
        con.commit()
    if rowcount == 0:
        logging.info("No new rows inserted into the database.")
    return rowcount




def process_source(name, url, parser):
    logging.info("Processing source: %s", name)
    content = fetch(url)
    if content is None:
        logging.warning("No response.")
        return False
    job_listings = parser(content)
    if not job_listings:
        logging.warning("Nothing was scraped")
        return False
    load(job_listings)
    return True

def get_new_cards(con,n=5):
    cur=con.cursor()
    cur.execute("""SELECT title,company_name,location,tags,link,applied_at FROM jobs ORDER BY scraped_at DESC LIMIT ?""",(n,))
    res=cur.fetchall()
    return res

def mark_applied(con,link):
    cur=con.cursor()
    cur.execute("UPDATE jobs SET applied_at=? WHERE link=? AND applied_at IS NULL",(dt.now().isoformat(),link))
    con.commit()
    return cur.rowcount


def search_jobs(con,q):
    v="%"+q+"%"
    cur=con.cursor()
    cur.execute("""SELECT title,company_name,location,tags,link,applied_at FROM jobs 
    WHERE (title LIKE ? OR
    company_name LIKE ? OR
    location LIKE ? OR
    tags LIKE ?) AND applied_at IS NULL ORDER BY scraped_at DESC""",(v,v,v,v))
    res=cur.fetchall()
    return res  

def export_showcase(src_conn,path="showcase.db"):
    if os.path.exists(path):
        os.remove(path)
    rows=src_conn.execute("SELECT title,company_name,location,link,source,scraped_at,tags FROM jobs")
    data=rows.fetchall()
    with closing(sqlite3.connect(path)) as con:
        cur=con.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS jobs(
                    title TEXT,
                    company_name TEXT,
                    location TEXT,
                    link  TEXT NOT NULL UNIQUE,
                     source TEXT,
                      scraped_at TEXT,
                       tags TEXT )""")
        cur.executemany("""INSERT OR IGNORE INTO
        jobs(title,company_name,location,link,source,scraped_at,tags)
        VALUES(?,?,?,?,?,?,?)""",data)
        con.commit()
        return cur.rowcount



def main():
    url1 = "https://weworkremotely.com/remote-jobs"
    url2 = "https://remoteok.com/api"
    sources = [
        ("weworkremotely", url1, parse_html),
        ("remoteok", url2, parse_json),
    ]
    count = 0
    for name, url, parser in sources:
        succeeded = process_source(name, url, parser)
        if succeeded:
            count += 1
    if count == 0:
        sys.exit(1)
    #Menu driven program
    with closing(sqlite3.connect(DB_PATH)) as con:
        while True:
            print("\n--- Main Menu ---")
            print("1. Get newest cards")
            print("2. Mark applied_at")
            print("3. Search jobs")
            print("4. Export_showcase")
            print("5. Exit")
            
            print("6: Invalid choice")
            choice = input("Enter your choice (1-5): ")
            if choice=="1":
                newest_cards=get_new_cards(con)
                print(newest_cards)
            elif choice=="2":
                link = input("Enter the job link: ").strip()
                marked = mark_applied(con, link)
                print("Marked applied." if marked else "Not found or already applied.")
            elif choice=="3":
                q = input("Enter search term: ").strip()
                for row in search_jobs(con, q):
                    print(row)
            elif choice=="4":
                showdb_rowcount=export_showcase(con)
                print(showdb_rowcount)
            elif choice=="5":
                break
            else:
                print("Invalid choice.")


if __name__ == "__main__":
    main()
   

import sqlite3
import sys
import requests
import logging
from bs4 import BeautifulSoup
logging.basicConfig(
    filename="pipeline.log",
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
response=requests.get("https://weworkremotely.com/remote-jobs",headers=headers)
if response.status_code!=200:
    logging.error("Inaccesible link")
    sys.exit(1)
soup=BeautifulSoup(response.content,'html.parser')
divs=soup.find_all("div",class_="new-listing")
#Creating list of jobs
jobs_list=[]
for ay in divs:
    job={}
    title=ay.find("span",class_="new-listing__header__title__text")
    if title is not None:
        job["title"]=title.get_text(strip=True)
    else:
        job["title"]="Unknown"
    company_name=ay.find("p",class_="new-listing__company-name")
    if company_name is not None:
        job["company name"]=company_name.get_text(strip=True)
    else:
        job["company name"]="Unknown"
    location=ay.find("p",class_="new-listing__company-headquarters")
    if location is not None:
        job["location"]=location.get_text(strip=True)
    else:
        job["location"]="Unknown"
    jobs_list.append(job)
logging.info("List of jobs: ")
logging.info(jobs_list)
logging.info(f"Successfully inserted {len(jobs_list)} jobs into the database.")
#Creating a database
con=sqlite3.connect("jobs.db")
cur=con.cursor()
cur.execute('''CREATE TABLE IF NOT EXISTS 
jobs(title TEXT UNIQUE,
company_name TEXT,
location TEXT)''')
for i in jobs_list:
    cur.execute('''
    INSERT OR IGNORE INTO jobs(title,company_name,location) 
    VALUES (?,?,?)
    ''',(i["title"],i["company name"],i["location"]))
con.commit()
con.close()

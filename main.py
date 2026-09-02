import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
def fetch(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
        response=requests.get(url,headers=headers,timeout=5)
        if response.content!=None:
            return response.content
        else:
            return None
    except requests.exceptions.RequestException as e:
        logging.warning("Error Occured : %e",e)

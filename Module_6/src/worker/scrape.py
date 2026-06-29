"""this is tnhe main module to scrape data"""

# pylint: disable=duplicate-code

from urllib.parse import urljoin
import time
import urllib3
import certifi
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service


# %%
http = urllib3.PoolManager(
    ca_certs=certifi.where()
)

# # since each page has around 50 records, I need to scrape around 1000 pages to reach 50000 records

BASE_URL= "https://www.thegradcafe.com"

def scrape_data(base_url=BASE_URL, start_page=1, end_page=5):# pylint: disable=too-many-locals
    """
    this function scrapes data using selenium
    and uses beautiful soup to parse the html
    """
    # driver = webdriver.Chrome()# pylint: disable=not-callable
    options = Options()
    options.binary_location = "/usr/bin/chromium"
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--user-data-dir=/tmp/chrome-user-data")

    service = Service("/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)
    raw_data = []

    try:
        for page in range(start_page, end_page + 1):
            print(f"\nScraping page {page}")
            driver.get(f"https://www.thegradcafe.com/survey?page={page}")

            WebDriverWait(driver, 60).until(
                EC.presence_of_element_located((By.TAG_NAME, "table"))
            )
            soup = BeautifulSoup(driver.page_source, "html.parser")
            # find table
            table = soup.find("table")
            # find header
            headers = [th.get_text(" ", strip=True) for th in table.find_all("th")]
            # print("Headers:", headers)
            current_record = None

            for tr in table.find_all("tr"):
                cells = tr.find_all("td")
                if not cells:
                    continue
                # find raw text then quote with " "
                cell_texts = [cell.get_text(" ", strip=True) for cell in cells]
                # Main row: School, Program, Added On, Decision, Sort
                if len(cell_texts) == len(headers):
                    link_tag = tr.find("a", href=True)
                    applicant_entry_url = urljoin(base_url, link_tag["href"]) if link_tag else None
                    cell_map = dict(zip(headers, cell_texts))
                    current_record = {
                        "page_number": page,
                        "School": cell_map.get("School"),
                        "Program": cell_map.get("Program"),
                        "Added On": cell_map.get("Added On"),
                        "Decision": cell_map.get("Decision"),
                        "applicant_entry_url": applicant_entry_url,
                        "extra_info": None,# placeholder
                        "comments": None,# placeholder
                        "raw_texts": cell_texts
                    }

                    raw_data.append(current_record)
                # Other info/comment rows below the main row
                # else if means --- If this row is not a normal main row, but we already have a
                # previous applicant record, then treat this row as extra information for that
                # previous applicant.”
                elif current_record is not None:
                    extra_info = " ".join(cell_texts)
                    if current_record["extra_info"] is None:
                        current_record["extra_info"] = extra_info
                    # If this applicant already has extra_info, then this next extra row
                    # is probably the comment.”
                    else:
                        current_record["comments"] = extra_info
            time.sleep(3)
    # finally:
    #     driver.quit()
    finally:
        try:
            driver.close()  # Close current tab first
            driver.quit()
        except Exception as e:# pylint: disable=broad-exception-caught
            print(f"Error closing driver: {e}")
    print("Total records:", len(raw_data))
    return raw_data

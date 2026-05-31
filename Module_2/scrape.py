
from curses import raw
import json
import urllib3
from urllib.parse import urljoin
import certifi
from bs4 import BeautifulSoup

import time 

http = urllib3.PoolManager(
    ca_certs=certifi.where()
)

url= "https://www.thegradcafe.com"
response = http.request("GET", url)
print(response.status)

html = response.data.decode("utf-8")
print(html[:1000])

soup = BeautifulSoup(html, "html.parser")
text = soup.get_text()
spaceless_text = text.replace("\n\n", "")
print(spaceless_text)

# get the Page title
print(soup.title.string) 

#------------ use beautiful soup to find all hyperlinks on this page -----------#

for link in soup.find_all("a"):   #Find all HTML <a> (anchor) tags in the page."
    text = link.get_text(strip=True)  #get all the text
    print(text)

#------------- use beautiful soup to find hyperlink for admissions ------------#
# for link in soup.find_all("a"):   #Find all HTML <a> (anchor) tags in the page."
#     text = link.get_text(strip=True)  
#     if "Admissions" in text:
#         print("Text:", text)
#         results = link.get("href")  #get the URL from the href attribute of the <a> tag
#         print("URL :", results)

url_admissions = None

for link in soup.find_all("a"): #Find all HTML <a> (anchor) tags in the page."
    text = link.get_text(strip=True)
    href = link.get("href")  #Get the value of the href attribute from the HTML tag. 
    if text == "Admissions" and "blog" not in href:
        url_admissions = href
        break

print(url_admissions)
# https://www.thegradcafe.com/survey


#------------------------------ use selenium -----------------------------#
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

driver = webdriver.Chrome()

#  load a web page by navigating to the provided URL
driver.get(url_admissions)

# Wait until at least one result row appears
WebDriverWait(driver, 20).until(
    EC.presence_of_element_located((By.TAG_NAME, "table"))
)

html_test = driver.page_source #extract the rendered html

print("Page loaded")
print(html_test[:500])

# Close browser
driver.quit()


# check how much data has been downloaded
print(len(html_test))




# #---------------- parse the html with beautiful soup ------------------#

# soup = BeautifulSoup(html_test, "html.parser")

# print(soup.title.get_text())

# # find out how many rows on this page
# rows = soup.find_all("tr")
# print("Rows found:", len(rows))
# # 56

# print(rows[0].prettify())
# # ---------------------

# import pandas as pd
# import re


# rows = []

# # First, inspect all table rows
# for tr in soup.find_all("tr"):   #Find all HTML <tr> tags in the page. tr stands for "table row"
#     text = tr.get_text(" ", strip=True)  # " " means put a space between different text
#     # skip empty rows
#     if not text:
#         continue

#     print(text)
#     print("-" * 80)

#--------------------- scrape more pages -------------------------#

start_time = time.time() 

driver = webdriver.Chrome()

records = []

try:
    for page in range(1, 6):  # Pages 1 through 5

        url = f"https://www.thegradcafe.com/survey?page={page}"
        print(f"\nScraping page {page}")

        driver.get(url)

        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "table"))
        )

        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")

        rows = soup.find_all("tr")

        print(f"Found {len(rows)} rows")

        for tr in rows:
            text = tr.get_text(" ", strip=True)

            if not text:
                continue

            records.append({
                "page": page,
                "raw_text": text
            })

        time.sleep(1)

finally:
    driver.quit()

print("\nTotal records scraped:", len(records))





# -------version 2---------------------------
# start_time = time.time() 
base_url = "https://www.thegradcafe.com"

driver = webdriver.Chrome()
raw_data = []

try:
    for page in range(1, 2):
        url = f"https://www.thegradcafe.com/survey?page={page}"
        print(f"\nScraping page {page}")

        driver.get(url)

        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "table"))
        )

        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")

        rows = soup.find_all("tr")
        print(f"Rows found on page {page}: {len(rows)}")
        
        
        # for tr in rows:
        #     raw_text = tr.get_text(" ", strip=True)

        #     if not raw_text:
        #         continue
        if len(rows) > 1:
            print(rows[1].prettify())
        else:
            print("No example row found")

        for tr in rows:
            cells = tr.find_all("td")
            if not cells:
                continue

            raw_text = tr.get_text(" ", strip=True)
            if not raw_text:
                continue

            link_tag = tr.find("a", href=True)
            applicant_entry_url = urljoin(base_url, link_tag["href"]) if link_tag else None

            cell_texts = [cell.get_text(" ", strip=True) for cell in cells]

            print("Appending record")

            raw_data.append({"page_number": page,
                "cell_texts": cell_texts,
                "applicant_entry_url": applicant_entry_url})

        time.sleep(1.5)

finally:
    driver.quit()

print("Total records:", len(raw_data))
print(raw_data[:3])


# elasped = time.time() - start_time

# print(elasped)

# for i in raw_data:
#     print(i)


# ----------------------test-----------------------------------------#



BASE_URL = "https://www.thegradcafe.com"
SURVEY_URL = "https://www.thegradcafe.com/survey/?page={}"
MAX_PAGES = 5
OUTPUT_FILE = "gradcafe_results_5_pages.json"


def clean_text(text):
    """Remove extra spaces and line breaks."""
    return re.sub(r"\s+", " ", text).strip()


def scrape_data(max_pages=5):
    """
    Pulls raw data from Grad Cafe.
    Returns a list of raw row dictionaries.
    """

    driver = webdriver.Chrome()
    raw_records = []

    try:
        for page in range(1, max_pages + 1):
            url = SURVEY_URL.format(page)
            print(f"Scraping page {page}: {url}")

            driver.get(url)

            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "table"))
            )

            html = driver.page_source
            soup = BeautifulSoup(html, "html.parser")

            rows = soup.find_all("tr")
            print(f"Rows found on page {page}: {len(rows)}")

            for tr in rows:
                raw_text = clean_text(tr.get_text(" ", strip=True))

                if not raw_text:
                    continue

                link_tag = tr.find("a", href=True)
                entry_url = urljoin(BASE_URL, link_tag["href"]) if link_tag else None

                cells = tr.find_all("td")
                cell_texts = [
                    clean_text(cell.get_text(" ", strip=True))
                    for cell in cells
                ]

                raw_records.append({
                    "page_number": page,
                    "raw_text": raw_text,
                    "cell_texts": cell_texts,
                    "entry_url": entry_url
                })

            time.sleep(1.5)

    finally:
        driver.quit()

    return raw_records


def clean_data(raw_records):
    """
    Converts scraped raw data into a structured format.
    Returns a list of cleaned dictionaries.
    """

    cleaned_records = []

    for record in raw_records:
        raw_text = record["raw_text"]

        applicant_status = None
        text_lower = raw_text.lower()

        if "accepted" in text_lower:
            applicant_status = "Accepted"
        elif "rejected" in text_lower:
            applicant_status = "Rejected"
        elif "waitlisted" in text_lower:
            applicant_status = "Waitlisted"
        elif "interview" in text_lower:
            applicant_status = "Interview"

        cleaned_record = {
            "Program Name": None,
            "University": None,
            "Comments": None,
            "Date of Information Added to Grad Cafe": None,
            "URL link to applicant entry": record["entry_url"],
            "Applicant Status": applicant_status,
            "Accepted: Acceptance Date": None,
            "Rejected: Rejection Date": None,
            "Semester and Year of Program Start": None,
            "International / American Student": None,
            "GRE Score": None,
            "GRE V Score": None,
            "Masters or PhD": None,
            "GPA": None,
            "GRE AW": None,
            "raw_text": raw_text,
            "cell_texts": record["cell_texts"],
            "page_number": record["page_number"]
        }

        gpa_match = re.search(r"\bGPA[:\s]*([0-4]\.\d{1,3})\b", raw_text, re.IGNORECASE)
        if gpa_match:
            cleaned_record["GPA"] = gpa_match.group(1)

        gre_match = re.search(r"\bGRE[:\s]*(\d{3,4})\b", raw_text, re.IGNORECASE)
        if gre_match:
            cleaned_record["GRE Score"] = gre_match.group(1)

        gre_v_match = re.search(r"\bV[:\s]*(\d{2,3})\b", raw_text, re.IGNORECASE)
        if gre_v_match:
            cleaned_record["GRE V Score"] = gre_v_match.group(1)

        gre_aw_match = re.search(r"\bAW[:\s]*(\d(?:\.\d)?)\b", raw_text, re.IGNORECASE)
        if gre_aw_match:
            cleaned_record["GRE AW"] = gre_aw_match.group(1)

        if re.search(r"\bphd\b|\bph\.d\b", raw_text, re.IGNORECASE):
            cleaned_record["Masters or PhD"] = "PhD"
        elif re.search(r"\bmaster\b|\bms\b|\bm\.s\.\b", raw_text, re.IGNORECASE):
            cleaned_record["Masters or PhD"] = "Masters"

        if "international" in text_lower:
            cleaned_record["International / American Student"] = "International"
        elif "american" in text_lower or "domestic" in text_lower:
            cleaned_record["International / American Student"] = "American/Domestic"

        cleaned_records.append(cleaned_record)

    return cleaned_records


def save_data(cleaned_records, filename=OUTPUT_FILE):
    """
    Saves cleaned data into a JSON file.
    """

    output = {
        "source": "GradCafe",
        "records_scraped": len(cleaned_records),
        "records": cleaned_records
    }

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=4, ensure_ascii=False)

    print(f"Saved {len(cleaned_records)} records to {filename}")


def load_data(filename=OUTPUT_FILE):
    """
    Loads cleaned data from a JSON file.
    """

    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data


def main():
    start_time = time.time()

    raw_records = scrape_data(max_pages=MAX_PAGES)

    cleaned_records = clean_data(raw_records)

    save_data(cleaned_records, OUTPUT_FILE)

    loaded_data = load_data(OUTPUT_FILE)

    elapsed = time.time() - start_time

    print("Done.")
    print("Records loaded:", loaded_data["records_scraped"])
    print(f"Elapsed time: {elapsed:.2f} seconds")


if __name__ == "__main__":
    main()


# %%

import json
import urllib3
from urllib.parse import urljoin
import certifi
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import time 
import re

import pandas as pd

# %%
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

# %%
#------------ use beautiful soup to find all hyperlinks on this page -----------#

# for link in soup.find_all("a"):   #Find all HTML <a> (anchor) tags in the page."
#     text = link.get_text(strip=True)  #get all the text
#     print(text)

#------------- use beautiful soup to find hyperlink for admissions ------------#

url_admissions = None

for link in soup.find_all("a"): #Find all HTML <a> (anchor) tags in the page."
    text = link.get_text(strip=True)
    href = link.get("href")  #get the URL from the href attribute of the <a> tag
    if text == "Admissions" and "blog" not in href:
        url_admissions = href
        break

print(url_admissions)
# https://www.thegradcafe.com/survey


# %%
# #--------------------- scrape more pages, test how many  -------------------------#
# driver = webdriver.Chrome()

# records = []

# try:
#     for page in range(1, 6):  # Pages 1 through 5

#         url = f"https://www.thegradcafe.com/survey?page={page}"
#         print(f"\nScraping page {page}")

#         driver.get(url)

#         WebDriverWait(driver, 20).until(
#             EC.presence_of_element_located((By.TAG_NAME, "table"))
#         )

#         html = driver.page_source
#         soup = BeautifulSoup(html, "html.parser")

#         rows = soup.find_all("tr")

#         print(f"Found {len(rows)} rows")

#         for tr in rows:
#             text = tr.get_text(" ", strip=True)

#             if not text:
#                 continue

#             records.append({
#                 "page": page,
#                 "raw_text": text
#             })

#         time.sleep(1)

# finally:
#     driver.quit()

# print("\nTotal records scraped:", len(records))

# # since each page has around 50 records, I need to scrape around 1000 pages to reach 50000 records

# %%
def scrape_data(start_page=1, end_page=5):
    """
    this function scrapes data using selenium
    and uses beautiful soup to parse the html
    """
    base_url= "https://www.thegradcafe.com"

    driver = webdriver.Chrome()
    raw_data = []

    try:
        for page in range(start_page, end_page + 1):
            url = f"https://www.thegradcafe.com/survey?page={page}"
            print(f"\nScraping page {page}")

            driver.get(url)

            WebDriverWait(driver, 60).until(
                EC.presence_of_element_located((By.TAG_NAME, "table"))
            )

            html = driver.page_source
            soup = BeautifulSoup(html, "html.parser")
            
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
                        "extra_info": None,   # placeholder
                        "comments": None,     # placeholder
                        "raw_texts": cell_texts
                    }

                    raw_data.append(current_record)

                # Other info/comment rows below the main row
                # else if means --- If this row is not a normal main row, but we already have a previous applicant record, 
                # then treat this row as extra information for that previous applicant.”

                elif current_record is not None:
                    extra_info = " ".join(cell_texts)

                    if current_record["extra_info"] is None:
                        current_record["extra_info"] = extra_info
                    # If this applicant already has extra_info, then this next extra row is probably the comment.”
                    else:  
                        current_record["comments"] = extra_info
                        
            time.sleep(3)

    # finally:
    #     driver.quit()
    finally:
        try:
            driver.close()  # Close current tab first
            driver.quit()
        except Exception as e:
            print(f"Error closing driver: {e}")

    print("Total records:", len(raw_data))
    return raw_data


# %%
def save_data(cleaned_data, filename):
    """
    Saves cleaned data into a JSON file.
    """
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(cleaned_data, f, indent=4, ensure_ascii=False)

    print(f"Saved {len(cleaned_data)} records to {filename}")


def load_data(filename):
    """
    Loads cleaned data from a JSON file.
    """
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data

# %%
# # scrape data test

# scraped_raw_data = scrape_data(start_page=3000, end_page=3005)
# type(scraped_raw_data)

# save_data(scraped_raw_data, "scraped_data_test.json")

# %%
# this block was run for the first 1000 pages

# def main():
#     start_time = time.time()

#     raw_records = scrape_data(start_page=1, end_page=1000)

#     save_data(cleaned_data=raw_records, filename="json_data_part1.json")

#     elapsed = time.time() - start_time

#     print(f"Elapsed time: {elapsed:.2f} seconds")

# %%
# # this block was run for page 1000 to 2000.
# #  since timeoutexception happens a lot, I have to process in batches, and save small batches along the way
# def main():

#     # page 1001-2000, in smaller batches
#     start_time = time.time()
#     all_scraped_data = []
    
#     batch_size = 50  # Process 50 pages at a time
#     start_page = 1001
#     end_page = 2000
    
#     for batch_start in range(start_page, end_page + 1, batch_size):
#         batch_end = min(batch_start + batch_size - 1, end_page)
        
#         print(f"\n{'='*60}")
#         print(f"Processing batch: pages {batch_start} to {batch_end}")
#         print(f"{'='*60}")
        
#         try:
#             raw_records = scrape_data(start_page=batch_start, end_page=batch_end)
#             all_scraped_data.extend(raw_records)
            
#             # Save this batch
#             batch_filename = f"json_data_batch_{batch_start}_{batch_end}.json"
#             save_data(cleaned_data=raw_records, filename=batch_filename)
            
#         except Exception as e:
#             print(f"Error on batch {batch_start}-{batch_end}: {e}")
#             break
    
#     # Save all data combined
#     if all_scraped_data:
#         save_data(cleaned_data=all_scraped_data, filename="json_data_part2.json")
#         elapsed = time.time() - start_time
#         print(f"\nTotal elapsed time: {elapsed:.2f} seconds")
#         print(f"Total records: {len(all_scraped_data)}")

# %%
def main():

    # page 2001-2500, in smaller batches
    start_time = time.time()
    all_scraped_data = []
    
    batch_size = 50  # Process 50 pages at a time
    start_page = 2001
    end_page = 2500
    
    for batch_start in range(start_page, end_page + 1, batch_size):
        batch_end = min(batch_start + batch_size - 1, end_page)
        
        print(f"\n{'='*60}")
        print(f"Processing batch: pages {batch_start} to {batch_end}")
        print(f"{'='*60}")
        
        try:
            raw_records = scrape_data(start_page=batch_start, end_page=batch_end)
            all_scraped_data.extend(raw_records)
            
            # Save this batch
            batch_filename = f"json_data_batch_{batch_start}_{batch_end}.json"
            save_data(cleaned_data=raw_records, filename=batch_filename)
            
        except Exception as e:
            print(f"Error on batch {batch_start}-{batch_end}: {e}")
            break
    
    # Save all data combined
    if all_scraped_data:
        # save_data(cleaned_data=all_scraped_data, filename="json_data_part3.json")
        save_data(cleaned_data=all_scraped_data, filename="json_data_test3.json")
        elapsed = time.time() - start_time
        print(f"\nTotal elapsed time: {elapsed:.2f} seconds")
        print(f"Total records: {len(all_scraped_data)}")


# %%
if __name__ == "__main__":
    main()

# %% [markdown]
# ##### Combine all three parts together

# %%
with open("json_data_part1.json", "r", encoding="utf-8") as f:
    json_data_part1 = json.load(f)

with open("json_data_part2.json", "r", encoding="utf-8") as f:
    json_data_part2 = json.load(f)

with open("json_data_part3.json", "r", encoding="utf-8") as f:
    json_data_part3 = json.load(f)

all_scraped_data = json_data_part1 + json_data_part2 + json_data_part3

print(len(all_scraped_data))

save_data(cleaned_data=all_scraped_data, filename="all_scraped_data.json")


# %%
# with open("scraped_data_test.json", "r", encoding="utf-8") as f:
#     json_data_test1 = json.load(f)

# with open("json_data_test3.json", "r", encoding="utf-8") as f:
#     json_data_test3 = json.load(f)


# all_scraped_data = json_data_test1 + json_data_test3

# print(len(all_scraped_data))

# save_data(cleaned_data=all_scraped_data, filename="all_scraped_data_test.json")




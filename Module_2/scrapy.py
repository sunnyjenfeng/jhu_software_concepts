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
#------------------------------ test selenium, scrape one page only-----------------------------#

# driver = webdriver.Chrome()

# #  load a web page by navigating to the provided URL
# driver.get(url_admissions)

# # Wait until at least one result row appears
# WebDriverWait(driver, 20).until(
#     EC.presence_of_element_located((By.TAG_NAME, "table"))
# )

# html_test = driver.page_source #extract the rendered html

# print("Page loaded")
# print(html_test[:500])

# # Close browser
# driver.quit()


# # check how much data has been downloaded
# print(len(html_test))

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

# %% [markdown]
# #### Scrape data

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
# # check data so far
# for i in raw_data[:3]:
#     print(i)

# %% [markdown]
# #### Clean data

# %%
def clean_space(value):
    """ 
    this function collapses multiple white spaces into one
    remove leading space and trailing space
    """
    if value is None:
        return None
    value = re.sub(r"\s+", " ", str(value)).strip()
    return value if value else None


def extract_status(text):
    """ 
    this function detects the applicant status from the text, and return one of 
    the following categories
    """
    if text is not None: 
        text_lower = text.lower()

        if "not accepted" in text_lower:
            return None
        if "accepted" in text_lower:
            return "Accepted"
        if "rejected" in text_lower:
            return "Rejected"
        if "wait listed" in text_lower or "waitlisted" in text_lower:
            return "Waitlisted"
        if "interview" in text_lower:
            return "Interview"
    return None


def extract_decision_date(text):
    if text is None:
        return None

    match = re.search(
        r"\b(?:Accepted|Rejected|Interview|Wait listed|Waitlisted)\s+on\s+([A-Za-z]{3,9}\s+\d{1,2})",
        text,
        re.IGNORECASE)
    return match.group(1) if match else None


def extract_term(text):
    text = text or ""
    match = re.search(r"\b(Fall|Spring|Summer|Winter)\s+(20\d{2})\b", text, re.IGNORECASE)
    if match:
        return f"{match.group(1).title()} {match.group(2)}"
    return None


def extract_student_type(text):
    if text is None:
        return None
    
    text_lower = text.lower()

    if "international" in text_lower:
        return "International"
    if "american" in text_lower or "domestic" in text_lower:
        return "American"
    if "other" in text_lower:
        return "Other"
    return None


def extract_gpa(text):
    text = text or ""
    match = re.search(r"\bGPA\s*[: ]\s*([0-4](?:\.\d{1,3})?)\b", text, re.IGNORECASE)
    return match.group(1) if match else None


def extract_gre_score(text):
    text = text or ""
    match = re.search(r"\bGRE\s+(\d{2,3})\b", text, re.IGNORECASE)
    return match.group(1) if match else None


def extract_gre_v(text):
    text = text or ""
    match = re.search(r"\bGRE V\s+(\d{2,3})\b", text, re.IGNORECASE)
    return match.group(1) if match else None


def extract_gre_aw(text):
    text = text or ""
    match = re.search(r"\bGRE AW\s+(\d(?:\.\d{1,2})?)\b", text, re.IGNORECASE)
    return match.group(1) if match else None


def extract_degree(program):
    program = program or ""

    if "phd" in program.lower():
        return "PhD"
    if "masters" in program.lower() or "master" in program.lower():
        return "Masters"

    return None

def clean_data(raw_data):
    """
    this is the function to clean the raw data
    """
    cleaned_data = []

    for data in raw_data:
        extra_info = clean_space(data["extra_info"])
        comments = clean_space(data["comments"])
        decision_clean = clean_space(data["Decision"])

        combined_text = " ".join([
            text for text in [decision_clean, extra_info, comments]
            if text])
        # two possible places to extract status
        status = extract_status(decision_clean) or extract_status(extra_info)
        decision_date = extract_decision_date(decision_clean) or extract_decision_date(extra_info)

        cleaned_data.append({
            "Program Name": clean_space(data["Program"]),
            "University": clean_space(data["School"]),
            "Comments": comments,
            "Date of Information Added to Grad Cafe": clean_space(data["Added On"]),
            "URL link to applicant entry": data["applicant_entry_url"],
            "Applicant Status": status,
            "Accepted: Acceptance Date": decision_date if status == "Accepted" else None,
            "Rejected: Rejection Date": decision_date if status == "Rejected" else None,
            "Semester and Year of Program Start": extract_term(combined_text),
            "International / American Student": extract_student_type(combined_text),
            "GRE Score": extract_gre_score(combined_text),
            "GRE V Score": extract_gre_v(combined_text),
            "Masters or PhD": extract_degree(data["Program"]),
            "GPA": extract_gpa(combined_text),
            "GRE AW": extract_gre_aw(combined_text),
            "extra_info": extra_info,
            "raw_texts": data["raw_texts"],
            "page_number": data["page_number"]
        })
    return cleaned_data

# df_cleaned = pd.DataFrame(cleaned_data)
# df_cleaned.head()

# %% [markdown]
# #### Save data and load data

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
# this block was run for the first 1000 pages

# def main():
#     start_time = time.time()

#     raw_records = scrape_data(start_page=1, end_page=1000)
#     cleaned_data = clean_data(raw_records)

#     save_data(cleaned_data=cleaned_data, filename="json_data_part1.json")

#     loaded_data = load_data(filename="json_data_part1.json")

#     elapsed = time.time() - start_time

#     print(f"Elapsed time: {elapsed:.2f} seconds")

# %%
# this block was run for page 1000 to 2000.
#  since timeoutexception happens a lot, I have to process in batches, and save small batches along the way
# def main():
#     # page 1001-2000, in smaller batches
#     start_time = time.time()
#     all_cleaned_data = []
    
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
#             cleaned_data = clean_data(raw_records)
#             all_cleaned_data.extend(cleaned_data)
            
#             # Save this batch
#             batch_filename = f"json_data_batch_{batch_start}_{batch_end}.json"
#             save_data(cleaned_data=cleaned_data, filename=batch_filename)
            
#         except Exception as e:
#             print(f"Error on batch {batch_start}-{batch_end}: {e}")
#             break
    
#     # Save all data combined
#     if all_cleaned_data:
#         save_data(cleaned_data=all_cleaned_data, filename="json_data_part2.json")
#         elapsed = time.time() - start_time
#         print(f"\nTotal elapsed time: {elapsed:.2f} seconds")
#         print(f"Total records: {len(all_cleaned_data)}")


# %%
def main():

    # page 2001-2500, in smaller batches
    start_time = time.time()
    all_cleaned_data = []
    
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
            cleaned_data = clean_data(raw_records)
            all_cleaned_data.extend(cleaned_data)
            
            # Save this batch
            batch_filename = f"json_data_batch_{batch_start}_{batch_end}.json"
            save_data(cleaned_data=cleaned_data, filename=batch_filename)
            
        except Exception as e:
            print(f"Error on batch {batch_start}-{batch_end}: {e}")
            break
    
    # Save all data combined
    if all_cleaned_data:
        save_data(cleaned_data=all_cleaned_data, filename="json_data_part3.json")
        elapsed = time.time() - start_time
        print(f"\nTotal elapsed time: {elapsed:.2f} seconds")
        print(f"Total records: {len(all_cleaned_data)}")


# %%
if __name__ == "__main__":
    main()

# %%
# combine all three parts of data, and check how many records in total
# applicant_data is the final dataset

with open("json_data_part1.json", "r", encoding="utf-8") as f:
    json_data_part1 = json.load(f)

with open("json_data_part2.json", "r", encoding="utf-8") as f:
    json_data_part2 = json.load(f)

with open("json_data_part3.json", "r", encoding="utf-8") as f:
    json_data_part3 = json.load(f)

applicant_data = json_data_part1 + json_data_part2 + json_data_part3

print(len(applicant_data))



# %%
save_data(cleaned_data=applicant_data, filename="applicant_data.json")

# loaded_data = load_data(filename="applicant_data.json")

# %%
# loaded_data = load_data(filename="/Users/jennifer/Documents/software_concept_python_class/jhu_software_concepts/Module_2/llm_hosting/out.json")



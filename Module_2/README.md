#Name: Jennifer Feng

#JHU ID: jfeng63

#Module Info: 
Module 2- Web Scraping   
Assignment: Web Scraping  
Due data: Sunday by 11:59pm


#Approach

1. Check robots.txt by going to https://www.thegradcafe.com/robots.txt
   A screenshot is shown as screenshot_robot.png in the folder.
   As a user, below are directories that I can not access
   
   User-agent: *
    Disallow: /signin
    Disallow: /register
    Disallow: /forgot-password
    Disallow: /reset-password
    Disallow: /confirm-password
    Disallow: /verify-email
    Disallow: /profile

2. (old version:  Scrapy.py includes all the functions: scrape_data(), clean_data(), save_data(), and save_data() )
   Scrapy.py was split into two .py files: scrape.py and clean.py. Please use these two files instead of scrapy.py

   scrape.py:  2a: uses urllib3 to construct, inspect, and manage Grad Cafe URLs. Find the url for admissions data. 
               It then uses selenium to scrape data from the url, and use beatifulsoup and regex to clean data. The  output of scrape.py is all_scraped_data.json. It scraped 41000 graduate applicant entries in total.

               2b: Chrome + ChromeDriver were used

               2c: Since timeoutexception happens a lot, I had to process in batches, and save small batches(batch size=50) along the way. It later combined all the saved json into one json. 

               2d: The detailed procedures are: I run the first def main() block for page 1-1000. then commented out this block of code. Then I created a second def main() to run for page 1001-2000. Then commented out the code. Then I created a third def main() to run for page 2001-2500. 

               2e: Then  all_scraped_data = json_data_part1 + json_data_part2 + json_data_part3


3. clean.py: load all_scraped_data.json and clean data using beaituful soup and regex/string methods.  
             The output is applicant_data.json (41000 records)      

4. Clean applicant_data.json using an LLM (tiny llama)
   For some reason using this step to clean up the data takes much longer time than I expected, even though I have tried to parallelize the processing. 

   The program is still running (it is working) . So I have pushed part of my llm processed data into Github to show it works. Test data name: 
   llm_extend_applicant_data_part1.json


#Please note: 
when I pushed llm_hosting to github, error shows the tiny llama model size was too big. So I had to push everything except the model. 


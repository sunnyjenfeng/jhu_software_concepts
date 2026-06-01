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

2. Scrapy.py includes all the functions: scrape_data(), clean_data(), save_data(), and save_data(). 
This code first uses urllib3 to construct, inspect, and manage Grad Cafe URLs. Find the url for admissions data. 
3. It then uses selenium to scrape data from the url, and use beatifulsoup and regex to clean data. The  output of scrapy.py is applicant_data.json. It scraped 41000 graduate applicant entries in total.
  3a: Chrome + ChromeDriver were used

  3b: Since timeoutexception happens a lot, I had to process in batches, and save small batches(batch size=50) along the way. It later combined all the saved json into one named applicant_data.json. 

  3c: The detailed procedures are: I run the first def main() block for page 1-1000. then commented out this block of code. Then I created a second def main() to run for page 1001-2000. Then commented out the code. Then I created a third def main() to run for page 2001-2500. 

  3d: Then  applicant_data = json_data_part1 + json_data_part2 + json_data_part3

4. Clean applicant_data.json using an LLM (tiny llama)
5. The final data set is llm_extend_applicant_data.json 


#Please note: 
There is no known bugs. 
Using tinyllama to clean up the data takes much longer time than I expected, even though I have tried to parallelize the processing. 

Using LLM to clean data is still in progress

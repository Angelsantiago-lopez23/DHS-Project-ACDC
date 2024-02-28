"""
State: Florida, County: Browad, Type: Broward Revenue Collection -> Records, Taxes, & Treasury
Input: Person of Interest
Output: Person Information --> Account Number, Owner, Address

NOTE: Prereq: pip install -r requirements.txt
"""

# Libraries Needed 
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager # NOTE: To avoid manually downloading binary dep. for browser.
from selenium.webdriver.common.by import By # NOTE: Needed for searching elements in html.
from selenium.webdriver.common.keys import Keys # NOTE: Be able to click enter, arrows, etc.
from selenium.webdriver.support.ui import WebDriverWait # NOTE: Waits for an element to exist. Goes with import below. (EC)
from selenium.webdriver.support import expected_conditions as EC 
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import pandas as pd # NOTE: Send collected data into df --> excel
#import numpy as np
import time # NOTE: To wait. 
import re # NOTE: Library for search pattern or in this case to validate input

def driver_initalization():
    return webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))

def website_target(driver, url):
    driver.get(url)

def validate_userinput(target_name):
    pattern = r'^[a-zA-Z\s]+$'
    if re.match(pattern, target_name):
        return True
    return False

def validate_searchresults(driver):
    try: 
        driver.find_element(By.XPATH, '')
        return True
    except NoSuchElementException:
        return False
    
def searchbox_person(driver, name):
    

def main():
    while True: 
        target_name = input("Format: 'Last Name, Firt Name'\nEnter the name to search: ")
        if not validate_user_input(target_name):
            print("Invalid Input...Please enter only alphabetical characters/spaces!")
            continue
        driver = driver_initalization()
        website_target(driver, '')
        searchbox_person(driver, target_name)
        if not validate_searchresults(driver):
            print("No search results found for the targeted name! Please try again!")
            driver.quit()
            continue
        all_data = multiple_pages(driver)
        driver.quit()
        data_to_excel(all_data, f"{target_name.replace(' ', '')}_output.xlsx")

        break


if __name__ == "__main__":
    main()

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
from selenium.webdriver.common.action_chains import ActionChains # Error with pagnation

import time # NOTE: To wait. 
import re # NOTE: Library for search pattern or in this case to validate input
from urllib.parse import urlparse, parse_qs, urlunparse, urlencode # Added to go with Carlos extract 

def driver_initialization():
    return webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))

def website_target(driver, url):
    driver.get(url)

def validate_user_input(target_name):
    pattern = r'^[a-zA-Z\s]+$'
    if re.match(pattern, target_name):
        return True
    return False

def validate_search_results(driver, wait_time=60):
    try:
        part1 = "No bills or accounts matched your search."
        part2 = "Try using different or fewer search terms."
        part3 = "The following tips may also help:"
        full_text = part1 + " " + part2 + " " + part3
        no_results_xpath = f"//p[text()='{full_text}']"

        for _ in range(wait_time):
            try:
                no_results = WebDriverWait(driver, 0.5).until(EC.presence_of_element_located((By.XPATH, no_results_xpath)))
                return False
            except Exception:
                pass

            try:
                results_class = 'category-search-results'
                WebDriverWait(driver, 0.5).until(EC.presence_of_element_located((By.CLASS_NAME, results_class)))
                return True
            except Exception:
                pass
        return False
    except Exception as e:
        print(f"Error occurred while validating search results: {e}")
        return False
    
def searchbox_person(driver, name):
    try:
        input_element = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//input[starts-with(@placeholder, 'Enter a name')]")))
        input_element.click()
        time.sleep(1)
        input_element.send_keys(name + Keys.ENTER)
        time.sleep(5)
    except Exception as e:
        print(f"Error occurred while searching: {e}")

def extract_data(driver):
    data = []
    try:
        div = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'category-search-results')))
        divs = div.find_elements(By.CLASS_NAME, 'content-card.my-2.mx-3.py-3.px-4')
        
        for div in divs:
            account = div.find_element(By.CLASS_NAME, 'identifier').text.strip().strip(',')
            account = account.replace('Account', '')
            owners = div.find_element(By.CLASS_NAME, 'name').text.strip().strip(',')

            billing_name_address, owner_address, address = 'NULL', 'NULL', 'NULL'

            address_elements = div.find_elements(By.CLASS_NAME, 'address')

            for address_element in address_elements:
                label = address_element.find_element(By.CLASS_NAME, 'label').text
                address_text = address_element.text.replace(label, '').strip().strip(',')
                if label == "BILLING ADDRESS":
                    billing_name_address = address_text
                elif label == "OWNER/ADDRESS":
                    # Split the address text by line breaks and concatenate each part separately
                    parts = address_text.split('\n')
                    if len(parts) > 1:
                        owner_name, owner_address = parts[0], ' '.join(parts[1:])
                    else:
                        owner_name, owner_address = parts[0], ''
                elif label == "ADDRESS":
                    address = address_text

            data.append([account, owners, owner_name.strip(), owner_address.strip(), address.strip(), billing_name_address])
    except Exception as e:
        print(f"Error occurred during data extraction: {e}")

    return data


"""def extract_data(driver):
    data = []
    try:
        div = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'category-search-results')))
        divs = div.find_elements(By.CLASS_NAME, 'content-card.my-2.mx-3.py-3.px-4')
        
        for div in divs:
            account = div.find_element(By.CLASS_NAME, 'identifier').text.strip().strip(',')
            account = account.replace('Account', '')
            owners = div.find_element(By.CLASS_NAME, 'name').text.strip().strip(',')

            billing_name_address, owner_address, address = 'NULL', 'NULL', 'NULL'

            address_elements = div.find_elements(By.CLASS_NAME, 'address')

            for address_element in address_elements:
                label = address_element.find_element(By.CLASS_NAME, 'label').text
                address_text = address_element.text.replace(label, '').strip().strip(',')

                if label == "BILLING ADDRESS":
                    billing_name_address = address_text
                elif label == "OWNER/ADDRESS":
                    owner_address = address_text.replace(owners, '').strip().strip(',')
                elif label == "ADDRESS":
                    address = address_text

            data.append([account, owners, owner_address, address, billing_name_address])
    except Exception as e:
        print(f"Error occurred during data extraction: {e}")

    return data"""

def navigate_to_next_page(driver, current_page_number):
    try:
        pagination_nav = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//nav[@aria-label='Pagination']")))
        ul = pagination_nav.find_element(By.TAG_NAME, 'ul')
        list_items = ul.find_elements(By.TAG_NAME, 'li')

        for item in list_items:
            if item.text == str(current_page_number + 1):
                item.click()
                return True

        return False
    except Exception as e:
        print(f"Error occurred during pagination: {e}")
        return False

def multiple_pages(driver, current_page_number):
    all_data = []
    try:
        while True:
            data = extract_data(driver)
            all_data.extend(data)
            if not navigate_to_next_page(driver, current_page_number):
                break
            else:
                current_page_number += 1
            time.sleep(5)
    except Exception as e:
        print(f"Error occurred during pagination: {e}")
    return all_data

def data_to_excel(data, output_file):
    try:
        df = pd.DataFrame(data, columns=['Account', 'Owners', 'Owner Address', 'Address', 'Billing Names & Address', 'random'])
        df.to_excel(output_file, index=False)
        print("Data has been written to:", output_file)
    except Exception as e:
        print(f"Error occurred while writing data to Excel: {e}")

def main():
    while True: 
        target_name = input("Format: 'Last Name, First Name'\nEnter the name to search: ")
        if not validate_user_input(target_name):
            print("Invalid Input...Please enter only alphabetical characters/spaces!")
            continue
        driver = driver_initialization()
        website_target(driver, 'https://broward.county-taxes.com/public/search/property_tax')
        searchbox_person(driver, target_name)
        if not validate_search_results(driver):
            print("No search results found for the targeted name! Please try again!")
            driver.quit()
            continue
        current_page_number = 1
        all_data = multiple_pages(driver, current_page_number)
        driver.quit()
        data_to_excel(all_data, f"{target_name.replace(' ', '')}_output.xlsx")
        break

if __name__ == "__main__":
    main()


"""
State: Florida, County: Browad, Type: Broward Revenue Collection -> Records, Taxes, & Treasury
Input: Person of Interest
Output: Person Information --> Account, Owner, Address, Billing Names & Address

*** During user input, a space after the full name leads to different results(shorter in the case of: "Smith John " ***
*** Used Lee: Tax Collector for guide since both website were created by the same group so outline almost identical***
NOTE: Prereq: pip install -r requirements.txt
     Have a input.xlsx file/excel with a 'Name' column. Then target names under that column.
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
from urllib.parse import urlparse, parse_qs, urlunparse, urlencode # To parse text and extract what is needed. 

def driver_initialization():
    """
    Initialize an instance for Chrome browser with ChromeDriveManager.
    """
    return webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))

def website_target(driver, url):
    """
    Get the target URL through driver. 
    """
    driver.get(url)

def validate_user_input(target_name):
    """
    Error handling: If user inputs numbers/symbols/others besides a last and first name --> invalid input until satisfied.
    Using the re: regular expression import. 
    """
    pattern = r'^[a-zA-Z\s]+$'
    if isinstance(target_name, str) and re.match(pattern, target_name):
        return True
    else:
        return False

def validate_search_results(driver, wait_time=60):
    """
    Checks if the search results are available or no matches/
    """
    try:
        # Into smaller texts 
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
                # Checking if search results is there or not. 
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
    """
    Wait for the search box even if it is available once in the website. 
    Then click in the search box and pass the targeted user and click enter.
    """
    try:
        input_element = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//input[starts-with(@placeholder, 'Enter a name')]")))
        input_element.click()
        time.sleep(1)
        input_element.send_keys(name + Keys.ENTER)
        time.sleep(5)
    except Exception as e:
        print(f"Error occurred while searching: {e}")

def extract_data(driver):
    """
    For this website, the results were not presented in a table like previous parts of Broward. In terms of having 
    table row, table cell, etc. 
    Used Lee:Tax Collector as reference. 
    *** Had error with getting the desired results. Removed owner variable since owner/address was broken into owner and address***
    Previously it was resulting in duplicate names and not complete address.
    """
    data = []
    try:
        div = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'category-search-results')))
        divs = div.find_elements(By.CLASS_NAME, 'content-card.my-2.mx-3.py-3.px-4') # Each target user in the target result page.
        
        for div in divs:
            account = div.find_element(By.CLASS_NAME, 'identifier').text.strip().strip(',')
            account = account.replace('Account', '')

            billing_name_address, owner_name, address = 'NULL', 'NULL', 'NULL'

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
                        owner_name, address = parts[0], ' '.join(parts[1:])
                    else:
                        address = parts[0]
                elif label == "ADDRESS":
                    address = address_text

            data.append([account, owner_name.strip(), address.strip(), billing_name_address])
    except Exception as e:
        print(f"Error occurred during data extraction: {e}")

    return data

def navigate_to_next_page(driver, current_page_number):
    """
    Used Lee: Tax collector for help but essentially relies on the pagination button to go to the next page of search results. 
    ***Before I tried using the arrow button and compare next result with prev page results to determine if we are on the last page. But didn't work out***
    
    """
    try:
        # Locate the pagination nav. element
        pagination_nav = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//nav[@aria-label='Pagination']")))
        ul = pagination_nav.find_element(By.TAG_NAME, 'ul')
        list_items = ul.find_elements(By.TAG_NAME, 'li')

        # Clicking the next page button.
        for item in list_items:
            if item.text == str(current_page_number + 1):
                item.click()
                return True

        return False    # We might on the last page. 
    except Exception as e:
        print(f"Error occurred during pagination: {e}") # Handling the error if no pagination nav exist. 
        return False

def multiple_pages(driver, current_page_number):
    """
    Extracting data in each 'next page'
    """
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
    """
    Using pandas to create a framework where we pass the extracted data and columns we need. Then creates
    an excel file. Also I passed less columns due to issue of 'owners' and 'owners/address'. As mentiioned above to 
    why I removed certain columns. 
    """
    try:
        df = pd.DataFrame(data, columns=['Account', 'Owners', 'Address', 'Billing Names & Address'])
        df.to_excel(output_file, index=False)
        print("Data has been written to:", output_file)
    except Exception as e:
        # Provides an error statement. 
        print(f"Error occurred while writing data to Excel: {e}")

def main():
    """
    Main loop where we utilize all functions to do the webscrapping on the website with the targeted user. 
    
    """
    while True: 
        try:
            file_path = './input.xlsx'
            file = pd.read_excel(file_path)
            names = file['Name'].tolist()
        except Exception as e:
            print(f"Error reading the input Excel file: {e}")
            continue

        for target_name in names: 
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

        print("Processing completed for all names in the input file.")
        break

if __name__ == "__main__":
    main()

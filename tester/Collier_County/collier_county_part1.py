"""
State: Florida, County: Collier, Type: Collier County Tax Collector
Input: Person of Interest
Output: Person Information --> Account, Owner, Address, Billing Names & Address

*** During user input, a space after the full name leads to different results(shorter in the case of: "Smith John " ***
*** Must create a input.xlsx and within a header named 'Name' and below the names of interest. Form 'LastName FirstName ***
NOTE: Prereq: pip install -r requirements.txt
"""

# Libraries Needed
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService # NOTE: To avoid manually downloading binary dep. for browser.
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By # NOTE: Needed for searching elements in html.
from selenium.webdriver.common.keys import Keys # NOTE: Be able to click enter, arrows, etc.
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import pandas as pd # NOTE: Send collected data into df --> excel
import time
import re # NOTE: Library for search pattern or in this case to validate input
from urllib.parse import urlparse, parse_qs, urlunparse, urlencode

def driver_initialization():
    """
    Initialize an instance for Chrome browser with ChromeDriveManager 
    """
    return webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))

def website_target(driver, url):
    """
    Get the target through URL 
    """
    driver.get(url)

def validate_user_input(target_name):
    """
    Error handling: If user inputs numbers/symbols/others besides a last and first name --> invalid input will raise alert.
    Using the re: regular expression import. 
    """
    pattern = r'^[a-zA-Z\s]+$'
    # isinstance is added to ensure that the target name passed is a string not an int
    if isinstance(target_name, str) and re.match(pattern, target_name):
        return True
    else:
        return False

def validate_searchresults(driver, wait_time=60):
    # Checks if the search results are available or no matches 
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
        time.sleep(3)
        input_element.send_keys(name + Keys.ENTER)
        time.sleep(5)
    except Exception as e:
        print(f"Error occurred while searching {e}")

def extract_data(driver):
    """
    Extracting the data from the results if user is found. Required more modification than other since it wasn't presented in a table like others. 
    At the end we append to data list.
    """
    data = []
    try:
        div = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "category-search-results")))
        divs = div.find_elements(By.CSS_SELECTOR, ".content-card.my-2.mx-3.py-3.px-4")

        for div in divs: 
            account = div.find_element(By.CLASS_NAME, "identifier").text.strip().replace('Account', '').strip()

            billing_name_address, owner_name, address = 'NULL', 'NULL', 'NULL'

            address_elements = div.find_elements(By.CLASS_NAME, "address")

            for address_element in address_elements:
                label = address_element.find_element(By.CLASS_NAME, 'label').text.strip()
                address_text = address_element.text.replace(label, '').strip()
                if label == "BILLING ADDRESS":
                    billing_name_address = address_text
                elif label == "OWNER/ADDRESS":
                    # Split the address text by line breaks and concatenate each part separately
                    parts = address_text.split('\n')
                    if len(parts) > 1:
                        owner_name, address = parts[0].strip(','), ' '.join(parts[1:]).strip(',')
                    else:
                        address = parts[0]
                elif label == "ADDRESS":
                    address = address_text

            data.append([account, owner_name, address, billing_name_address])
    except Exception as e:
        print(f"Error occurred during data extraction {e}")
    return data

def navigate_to_next_page(driver, current_page_number):
    """
    We utilized the pagination/button to go to the next page of search results. 
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
                time.sleep(2)
                return True
            
        return False # Might be on the last page
    except Exception as e:
        print(f"Error occurred during pagination: {e}")
        return False
    
def multiple_pages(driver, current_page_number):
    """
    If more than one page then we pass page number and extract the data of that page. 
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
        print(f"Error occured during pagination: {e}")
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
        print(f"Error occurred while writing data to Excel: {e}")

def main():
    """
    Main loop where we utilize all functions to do the webscrapping on the website with the list of targeted user. 
    NOTE: A modification is to pass an .excel that in turn we read and pass the names into a list. 
          Before it would just ask maually for user name in the command line but here it just read the file and runs the script. 
    """
    while True: 
        try:
            file_path = "./input.xlsx"
            file = pd.read_excel(file_path)
            names = file['Name'].tolist()  # Assuming the column name in the Excel file is 'Name'
        except Exception as e:
            print(f"Error reading the input Excel file: {e}")
            continue
        
        for target_name in names:
            if not validate_user_input(target_name):
                print(f"Invalid Input: {target_name}... Please ensure names contain only alphabetical characters and spaces!")
                continue
            driver = driver_initialization()
            website_target(driver, 'https://collier.county-taxes.com/public/search/property_tax')
            searchbox_person(driver, target_name)
            if not validate_searchresults(driver):
                print(f"No search results found for the name: {target_name}! Moving to the next name...")
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


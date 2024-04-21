# **** Date: 4/18/24 | Cleaned/deleted uncessary code and organized to be more readable. ****
"""

State: Florida ||| County: Broward County ||| Type: Records, Taxes, and Treasury
Input: Person of Interest
Output: Person Information(s) --> Collected(Appropriate Columns) --> Excel File

*** CREATE an input.xlsx that must include a column header named 'Name' and the 'Person of Interest' in the same column and in the format 'LastName FirstName' ***
*** NOTE: No comma between 'LastName FirstName' and spaces before or after the name besides separating 'LastName FirstName'
*** NOTE: Run 'pip install -r requirements.txt' for those wanting to debug/run file

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

# Initializing the Chrome Driver using the ChromeDriverManager to avoid downloading the appropriate Chrome Browser each time.
def driver_initialization():
    return webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))

def webscrape(driver, target_name):
    """
    REVAMPED:
        Before: There was no organization & difficult for others to follow process.
        After: Users should be able to follow it since the whole process of webscrapping is down below.
    PROCESS EXPLAINED: 
        - driver.get() --> we go to the designated website 
        - searchbox() --> after opening the website we locate the textbox and pass the target_name and press enter / print Exception if textbox not located
        - if not validate() --> after searchbox() function we check or validate if search results appeared. If returned True then continue with webscrape since 
          search results did appeared. if returned False then no search results appeared or error so no extraction of data occurs. 
        - declare all_data variable and a set_page_number to '1' since pagination is set to 1/first page
        - the data collected/extracted is added/executed in 'all_data = multiple_page()'
            - where multiple_pages() is a function that extracts the current page and if more pages than we add += 1 to the 'current_page_number' 
              which is added inside the multiple_page() function. Please refer to that function for more info.
        - after all data extraction done for all pages we return all the data colleted ('all_data')
        - now this function or the webscrape process is done
    """

    driver.get("https://broward.county-taxes.com/public/search/property_tax")

    searchbox(driver, target_name)

    if not validate(driver):
        return []
    
    all_data = []

    current_page_number = 1

    all_data = multiple_pages(driver, current_page_number)

    return all_data


def main():

    driver = driver_initialization()
    driver.maximize_window()

    while True:

        columns = ['Account', 'Owners', 'Address', 'Billing Names & Address']

        try:
            file_path = "./input.xlsx"
            file = pd.read_excel(file_path)
            names = file['Name'].tolist()
            all_data = []
        except Exception as e:
            print(f"Error reading the input Excel file: {e}")
            break

        for target_name in names: 

            data = webscrape(driver, target_name)
            all_data.extend(data)

        df = pd.DataFrame(all_data, columns=columns)
        df.to_excel("broward_records_taxes_treasury.xlsx", index=False)

        print("*** PROCESSING COMPLETED FOR ALL NAMES ***")
        break

    driver.quit()

# ------------ ABOVE: Main loop and the Webscrape Operation -------------- BELOW: The sub function operation that is executed when doing the WebScrape Operation ----

def searchbox(driver, target_name):

    try:
        input_element = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//input[starts-with(@placeholder, 'Enter a name')]")))
        input_element.click()
        time.sleep(3)
        input_element.send_keys(str(target_name) + Keys.ENTER)
        time.sleep(10)
    except Exception as e:
        print(f"Error occurred while searching {e}")


def validate(driver, wait_time=60):

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

def multiple_pages(driver, current_page_number):

    all_data = []

    try:
        while True:
            new_data = extract_data(driver)
            all_data.extend(new_data)

            if not navigate_to_next_page(driver, current_page_number):
                break
            else:
                current_page_number += 1
                time.sleep(5)
    except Exception as e:
        print(f"Error occured during pagination: {e}")

    return all_data


def extract_data(driver):

    data = []

    try:
        div = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'category-search-results')))
        divs = div.find_elements(By.CLASS_NAME, 'content-card.my-2.mx-3.py-3.px-4') # Each target user in the target result page.
        
        for div in divs:
            account = div.find_element(By.CLASS_NAME, 'identifier').text.strip().replace('Account', '').strip()

            billing_name_address, owner_name, address = 'NULL', 'NULL', 'NULL'

            address_elements = div.find_elements(By.CLASS_NAME, 'address')

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
        
        return False # might be on last page
    except Exception as e:
        print(f"Error occurred during pagination: {e}")
        return False
    
    
if __name__ == "__main__":
    main()










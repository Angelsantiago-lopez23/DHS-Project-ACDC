import logging
import os

# Prepare the log directory based on LOCALAPPDATA
log_dir = os.path.join(os.environ['LOCALAPPDATA'], 'cr-inspector', 'logs')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Specify the path for the log file within the prepared log directory
log_file_path = os.path.join(log_dir, 'lee_tax_collector_logs.txt')

# Configure logging to use the specified log file path
logging.basicConfig(
    level=logging.INFO,
    format='\n\n%(asctime)s - %(name)s - %(levelname)s - %(message)s\n\n',
    datefmt='%m/%d/%Y %I:%M:%S %p',
    filename=log_file_path,  # Use the full path instead of a relative one
    filemode='w'
)

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time
import json
import sys
import psutil

service = Service(ChromeDriverManager().install())
DRIVER = webdriver.Chrome(service=service)
main_process_pid = DRIVER.service.process.pid

def terminate_process_and_children(pid):
    try:
        parent = psutil.Process(pid)
        for child in parent.children(recursive=True):  # Recursively find child processes
            child.terminate()  # Terminate child process
        parent.terminate()  # Terminate the main process
    except psutil.NoSuchProcess:
        pass

def validate(wait_time=60):
    # Breaking down the long text into smaller strings
    part1 = "No bills or accounts matched your search."
    part2 = "Try using different or fewer search terms."
    part3 = "The following tips may also help:"
    full_text = part1 + " " + part2 + " " + part3
    no_results_xpath = f"//p[text()='{full_text}']"

    for _ in range(wait_time):
        try:
            # Checking for 'No matches found' message
            no_results = WebDriverWait(DRIVER, 0.5).until(EC.presence_of_element_located((By.XPATH, no_results_xpath)))
            return False
        except Exception:
            pass

        try:
            # Checking for the presence of the results
            results_class = 'category-search-results'
            WebDriverWait(DRIVER, 0.5).until(EC.presence_of_element_located((By.CLASS_NAME, results_class)))
            return True
        except Exception:
            pass
    return False

def extract_card_data(user_input):
    try:
        div = WebDriverWait(DRIVER, 15).until(EC.presence_of_element_located((By.CLASS_NAME, 'category-search-results')))
    except Exception as e:
        return []
    
    try:
        divs = div.find_elements(By.CLASS_NAME, 'content-card')
    except Exception as e:
        return []
    
    data = []
    
    for index in range(len(divs)):
        successful = False
        attempts = 0

        while not successful and attempts < 3:  # Retry up to 3 times for each card
            try:
                # Re-access the div since it may have become stale
                i = div.find_elements(By.CLASS_NAME, 'content-card')[index]

                account = i.find_element(By.CLASS_NAME, 'identifier').text.strip().strip(',').replace('Account', '')
                owners = i.find_element(By.CLASS_NAME, 'name').text.strip().strip(',')
                
                billing_name_address, owner_address, address = 'NULL', 'NULL', 'NULL'

                address_elements = i.find_elements(By.CLASS_NAME, 'address')
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
                successful = True  # Mark this card as successfully processed

            except StaleElementReferenceException:
                attempts += 1
                time.sleep(1)  # Briefly wait before retrying

            except Exception as e:
                successful = True  # Exit the retry loop, but this could be set to False if you want to keep trying irrespective of error type

    return data

def trying(function, attempts=3, delay=2):
    for _ in range(attempts):
        try:
            result = function()
            return result
        except Exception as e:
            time.sleep(delay)  # Wait for some time before retrying
    return False

def verify_click():
    for i in range(30):
        try:
            account_summary = WebDriverWait(DRIVER, 0.5).until(EC.presence_of_element_located((By.XPATH, "//div[@class='col-auto' and text()='Account Summary']")))
            return False
        except:
            pass

        try:
            pagination_nav = WebDriverWait(DRIVER, 0.5).until(EC.presence_of_element_located((By.XPATH, "//nav[@aria-label='Pagination']")))
            return True
        except:
            pass
        

def navigate_to_next_page(current_page_number):
    try:
        pagination_nav = WebDriverWait(DRIVER, 15).until(EC.presence_of_element_located((By.XPATH, "//nav[@aria-label='Pagination']")))
        ul = pagination_nav.find_element(By.TAG_NAME, 'ul')
        list_items = ul.find_elements(By.TAG_NAME, 'li')

        for item in list_items:
            if item.text == str(current_page_number + 1):
                # Scroll the pagination item into view
                DRIVER.execute_script("arguments[0].scrollIntoView(true);", item)
                time.sleep(1)  # Wait for scrolling to finish and any dynamic content to load

                # Ensure the item is clickable before clicking
                ActionChains(DRIVER).move_to_element(item).click().perform()
                time.sleep(1)

                if not verify_click():
                    return False

                if current_page_number + 1 == 18:
                    time.sleep(10)

                time.sleep(2)  # Wait for the page to load after clicking
                return True

        # If the next page button is not found, we might be on the last page
        return False
    except NoSuchElementException:
        # Handle the case where the pagination navigation is not found
        return False

def webscrape(user_input):
    # Navigating to the website and performing the search
    DRIVER.get("https://collier.county-taxes.com/public/search/property_tax")
    xpath = "//input[starts-with(@placeholder, 'Enter a name')]"
    name_field = WebDriverWait(DRIVER, 15).until(EC.presence_of_element_located((By.XPATH, xpath)))
    name_field.send_keys(user_input)
    name_field.send_keys(Keys.ENTER)

    time.sleep(2)

    if not validate():
        return []

    all_dfs = []
    current_page_number = 1
    while True:
        new_data = trying(lambda: extract_card_data(user_input), attempts=10, delay=0.5)
        all_dfs += new_data
        if not navigate_to_next_page(current_page_number):
            break
        else:
            current_page_number += 1
    return all_dfs

def main():
    columns=['Account', 'Owners', 'Owner Address', 'Address', 'Billing Names & Address']
    response = {"status": "success", "data": []}

    if len(sys.argv) < 2:
        response.update({"status": "error", "data": [{column: 'NULL' for column in columns}]})
        print(json.dumps(response))
        sys.exit(1)

    DRIVER.maximize_window()
    names = ','.join(sys.argv[1:]).split(',')
    all_dfs = []

    for name in names:
        try:
            data = webscrape(name)
            logging.info(data)
            if data:
                # Creating a DataFrame from the extracted data
                df = pd.DataFrame(data, columns=columns)

                df.fillna('NULL', inplace=True)
                df = df.astype(str)
                for column in columns:  # Ensure all expected columns are present
                    if column not in df.columns:
                        df[column] = 'NULL'
                df['Search Parameter'] = name
                all_dfs.extend(df.to_dict(orient="records"))
            else:
                # When appending empty or error data:
                structured_empty_data = [{column: 'NULL' for column in columns}]  # Use a list of one dict
                structured_empty_data[0]["Search Parameter"] = name
                all_dfs.extend(structured_empty_data)  # Extend appends each item in the list
        except Exception as e:
            # When appending empty or error data:
            structured_empty_data = [{column: 'NULL' for column in columns}]  # Use a list of one dict
            structured_empty_data[0]["Search Parameter"] = name
            all_dfs.extend(structured_empty_data)  # Extend appends each item in the list
    
    response["data"] = all_dfs
    print(json.dumps(response, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.info(e)
    finally:
        try:
            DRIVER.quit()
            terminate_process_and_children(main_process_pid)
        except:
            pass
        time.sleep(4) 

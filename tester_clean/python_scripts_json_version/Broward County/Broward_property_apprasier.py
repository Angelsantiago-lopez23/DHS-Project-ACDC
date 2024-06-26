# broward property_appraiser.py file:
import logging
import os

# Prepare the log directory based on LOCALAPPDATA
log_dir = os.path.join(os.environ['LOCALAPPDATA'], 'cr-inspector', 'logs')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Specify the path for the log file within the prepared log directory
log_file_path = os.path.join(log_dir, 'broward_property_appraiser_logs.txt')

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
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time
import sys
import json
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
    for _ in range(wait_time):
        try:
            # Checking for 'No matches found' message
            no_matches_id = 'ctl00_BodyContentPlaceHolder_WebTab1_tmpl0_ErrorLabel'
            no_matches = WebDriverWait(DRIVER, 0.5).until(EC.presence_of_element_located((By.ID, no_matches_id)))
            if "No matches found for given criteria" in no_matches.text:
                return False
        except Exception:
            pass

        try:
            # Checking for the presence of the results table
            results_class = 'resultsDataGrid'
            WebDriverWait(DRIVER, 0.5).until(EC.presence_of_element_located((By.CLASS_NAME, results_class)))
            return True
        except Exception:
            pass
    return False

def extract_table_data(user_input):
    table = WebDriverWait(DRIVER, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, "resultsDataGrid")))
    rows = table.find_elements(By.TAG_NAME, 'tr')
    data = []

    for row in rows:
        cols = row.find_elements(By.TAG_NAME, 'td')
        if cols:
            # Extracting various data fields from the table
            strap_folio = cols[0].text
            owner_info = cols[1]
            bold_elements = owner_info.find_elements(By.XPATH, ".//div[@class='bold']")
            bold_text = [elem.text.strip() for elem in bold_elements]
            owner_names = ' '.join(bold_text)

            owner_address = owner_info.text
            for owner_name in bold_text:
                owner_address = owner_address.replace(owner_name, '').strip()

            strap, folio = strap_folio.split('\n', 1)
            site_property_column = cols[2]
            divs = site_property_column.find_elements(By.CLASS_NAME, 'itemAddAndLegal')
            site_address = divs[0].text
            property_description = divs[1].text

            data.append([user_input, strap, folio, owner_names, owner_address, site_address, property_description])

    return data

def navigate_to_next_page(old_table_text):
    try:
        # Locating the page number dropdown and selecting the next page
        xpath = "//*[substring(@id, string-length(@id) - string-length('_pagenumberList') + 1) = '_pagenumberList']"
        select_element = WebDriverWait(DRIVER, 10).until(EC.element_to_be_clickable((By.XPATH, xpath)))
        select = Select(select_element)
        next_value = int(select.first_selected_option.get_attribute("value")) + 1
        select.select_by_value(str(next_value))

        end_time = time.time() + 60
        while True:
            try:
                new_table_text = DRIVER.find_element(By.CLASS_NAME, 'resultsDataGrid').text
                if new_table_text != old_table_text:
                    return True
            except StaleElementReferenceException:
                if time.time() > end_time:
                    return False
                continue
            time.sleep(0.5)
    except NoSuchElementException:
        return False

def webscrape(user_input):
    # Navigating to the website and performing the search
    DRIVER.get("https://web.bcpa.net/BcpaClient/#/Record-Search")
    name_field = WebDriverWait(DRIVER, 10).until(EC.element_to_be_clickable((By.ID, 'txtField')))
    name_field.send_keys(user_input)

    search_button = WebDriverWait(DRIVER, 10).until(EC.element_to_be_clickable((By.xpath, '/html/body/div[8]/div/div/div/div/div/div[2]/div[2]/div/div[1]/div[3]/div[2]/span/span')))
    search_button.click()

    if not validate():
        return []

    all_dfs = []
    while True:
        new_data = extract_table_data(user_input)
        all_dfs += new_data
        table_text = DRIVER.find_element(By.CLASS_NAME, 'resultsDataGrid').text
        if not navigate_to_next_page(table_text):
            break

    return all_dfs

def main():
    columns=['Name', 'Strap', 'Folio', 'Owners', 'Owners Address', 'Site Address', 'Property Description']

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
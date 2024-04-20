# **** Date: 4/20/24 | Cleaned/Deleted uneccessary code and organized to be more readable. ****
"""

State: Florida ||| County: Broward County ||| Type: Property Appraiser
Input: Person of Interest(s)
Output: Person Information --> Extract page(s) --> all_data --> Excel File

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
import time # NOTE: To wait. 

# Initializing the Chrome Driver using the ChromeDriverManager to avoid downloading the appropriate Chrome Browser each time.
def driver_initialization():
    return webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))

def webscrape(driver, target_name):
    """
    REVAMPED: 
        Before: Unorganized and difficult for some to follow or understand. 
        After: Made simpler and appropriate names for each function, etc
    PROCESS EXPLAINED: 
        - driver.get() --> Navigate to the designated website 
        - searchbox() --> Locate and click on textbox/ Raise error if can't --> Send target_name and ENTER
        - if not validate() --> Returns True if search results appeared otherwise return False that no search results appeared
        - initialize an empty all_data variable 
            - then perfom multiple_pages() where data is extracted on page(s) --> returned back to the data variable 
        - return all_data --> back to main --> excel
    """

    driver.get("https://web.bcpa.net/BcpaClient/#/Record-Search")

    searchbox(driver, target_name)

    if not validate(driver):
        return []
    
    all_data = []

    all_data = multiple_pages(driver)

    return all_data


def main():

    driver = driver_initialization()
    driver.maximize_window()

    while True: 
        columns = ['Folio', 'Name', 'Address']

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

        if all_data:
            df = pd.DataFrame(all_data, columns=columns)
            #df.map(replace_emptyvalues_with_null)
            df.to_excel('broward_property_appraiser.xlsx', index=False)
        else:
            pass

        print("*** PROCESSING COMPLETED FOR ALL NAMES ***")
        break

    driver.quit()

# ------------ ABOVE: Main loop and the Webscrape Operation -------------- BELOW: The sub function operation that is executed when doing the WebScrape Operation ----

def searchbox(driver, target_name):

    input_element = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, "form-control")))

    try: 
        time.sleep(1)
        input_element.clear()
        input_element.click()
        input_element.send_keys(str(target_name) + Keys.ENTER)
        time.sleep(6)

    except Exception as e:
        print(f"Error occurred while searching {e}")
    
def validate(driver, wait_time=60):

    for _ in range(wait_time):
        try:
            driver.find_element(By.XPATH, '//*[@id="tbl-list-parcels"]')
            time.sleep(2)
            return True
        except NoSuchElementException:
            pass
    return False

def multiple_pages(driver):

    all_data = []
    previous_data = []

    try:
        while True:
            no_records_element = driver.find_element(By.ID, 'noRecordFound')

            if no_records_element.is_displayed():
                #print("No records found for this name.") Commented out just for a clean look but can uncomment
                break

            new_data = extract_data(driver)

            if new_data == previous_data:
                break

            all_data.extend(new_data)
            previous_data = new_data[:]

            next_page_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="btnNextRecords"]')))

            if next_page_button:
                next_page_button.click()
                time.sleep(5)
            else:
                print("No more pages. Exiting...")
                break
            
    except (NoSuchElementException, TimeoutException):
        pass

    return all_data

def extract_data(driver):

    data = []

    try:
        tbody = driver.find_element(By.XPATH, '//*[@id="tbl-list-parcels"]/tbody')

        for tr in tbody.find_elements(By.XPATH, './/tr'):
            row = [item.text for item in tr.find_elements(By.XPATH, './/td')]
            data.append(row)
        
    except Exception as e:
        print(f"Error occurred during data extraction {e}")

    return data


if __name__ == "__main__":
    main()



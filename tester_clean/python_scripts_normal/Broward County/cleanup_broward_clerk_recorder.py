# **** Date: 4/20/24 | Cleaned/Deleted uneccessary code and organized to be more readable. ****
"""

State: Florida ||| County: Broward County ||| Type: Clerk/Recorder
Input: Person of Interest

Output: Person Information --> Extract Page(s) --> Repeat if more than 1 name --> Filter --> Excel File

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
        Before: No organization & difficulty for others to follow and duplication
        After: Users should be able to follow and understand the process. 
    PROCESS EXPLAINED: 
        - driver.get() --> Go to the designated website 
        - searchbox() --> After opening website --> Click Accept Conditions --> Click Textbox and send target_name --> Click Enter
        - if not validate() --> Returns True if search results appeared. Returns False if no search results appeared or other unexpected errors. 
        - declare the all_data variable 
        - following that multiple_pages() is executed function. --> inside is extract() function where page(s) is extracted 
        - extracted data stored in all_data
        - lastly return all_data back to main where appended --> pd --> dataframe --> all data into excel file/filtered

    """

    driver.get("https://officialrecords.broward.org/AcclaimWeb/search/Disclaimer?st=/AcclaimWeb/search/SearchTypeName")

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

        columns = ['Cart', 'Searched Name', 'Party Type', 'Related Name', 'Record Date', 
                    'Book Type', 'Book/Page', 'Instrument #', 'Comments2', 'Case #', 
                    'Consideration', 'Legal', 'Doc Type']
        
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
            df = df.drop(['Cart', 'Book Type'], axis=1)
            df = df.map(replace_emptyvalues_with_null)
            df.to_excel("broward_clerk_recorder.xlsx", index=False)
        else:
            pass
        
        print("*** PROCESSING COMPLETED FOR ALL NAMES ***")
        break

    driver.quit()

# ------------ ABOVE: Main loop and the Webscrape Operation -------------- BELOW: The sub function operation that is executed when doing the WebScrape Operation ----

def searchbox(driver, target_name):

    condition_element_before_search = WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.CLASS_NAME, "t-button")))
    time.sleep(1.5)

    try:
        condition_element_before_search.click()
        time.sleep(3)
    except:
        print("Error Accepting/Findings Conditions Button")
    
    input_element = WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="SearchOnName"]')))

    try:
        time.sleep(1.5)
        input_element.click()
        input_element.send_keys(str(target_name) + Keys.ENTER)
        time.sleep(10)
    except Exception as e:
        print(f"Error occurred while searching {e}")

def validate(driver, wait_time=60):

    for _ in range(wait_time):
        try:
            driver.find_element(By.XPATH, "//*[@id='RsltsGrid']/div[4]/table")
            time.sleep(3)
            return True
        except NoSuchElementException:
            # No results exist
            pass
        
    return False

def multiple_pages(driver):

    all_data = []
    previous_data = []

    try:
        while True:
            new_data = extract_data(driver)

            if new_data == previous_data:
                break

            all_data.extend(new_data)
            previous_data = new_data[:]

            next_page_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="RsltsGrid"]/div[2]/div[2]/a[3]/span')))

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
        tbody = driver.find_element(By.XPATH, '//*[@id="RsltsGrid"]/div[4]/table/tbody')

        for tr in tbody.find_elements(By.XPATH, './/tr'):
            row = [item.text for item in tr.find_elements(By.XPATH, './/td')]
            data.append(row)

    except Exception as e:
        print(f"Error occurred during data extraction {e}")

    return data

def replace_emptyvalues_with_null(value):
    if pd.isnull(value) or value == '':
        return 'NULL'
    else:
        return value
    
if __name__ == "__main__":
    main()



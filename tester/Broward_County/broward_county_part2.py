"""
State: Florida, County: Broward, Type: Clerk/Recorder
Input: Person of Interest
Output: Person Information --> Searched Name, Party Type, Related Name, Record Date, etc.

NOTE: Prereq: pip install -r requirements.txt
      Have a input.xlsx file/excel with the 'Name' column. Then target names under that columns for the scripts to read all names
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
import re # NOTE: Library for search pattern or in this case to validate input


def driver_initalization():
    """
    Initialize an instance for Chrome browser with ChromDriverManager.
    """
    return webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))

def website_target(driver, url):
    """
    Get the target URL through driver. 
    """
    driver.get(url)

def validate_userinput(target_name):
    """
    Error handling: If user inputs numbers/symbols/others besides a last and first name --> invalid input until satisfied.
    Using the re: regular expression import. 
    """
    pattern = r'^[a-zA-Z\s]+$'
    if isinstance(target_name, str) and re.match(pattern, target_name):
        return True
    else:
        return False

def validate_searchresults(driver):
    """
    Error handling: Checks if the user exist if so then continue if not then return False. 
    """
    try: 
        driver.find_element(By.XPATH, '//*[@id="RsltsGrid"]/div[4]/table')
        return True
    except NoSuchElementException:
        return False
    
def conditions_then_searchboxperson(driver, name):
    """
    Modification: For this website instead of going directly to search user page. It prompts a "accept terms/condition" page. 
                  So we have a variable with a wait for element to appear in a 10 second interval. After 10 seconds it checks for 
                  that element and then it clicks the element. 
    Next, takes you to search user page and a 1p second delay for the element to exist. Helps if the client has slow connection or element
    hasn't appeared. --> Click element and then send a key 'ENtER'
    """
    conditions_element = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, "t-button")))
    time.sleep(10)
    conditions_element.click()
    input_element = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="SearchOnName"]')))
    try:
        #conditions_element.click()
        #time.sleep(10)
        input_element.click()
        time.sleep(5)
    except:
        pass
    input_element.send_keys(name + Keys.ENTER)
    time.sleep(5)

def extract_data(driver):
    """
    The results in this website are given in a table. So we highlight the table element and then a for loop 
    for each row --> Then each table cell is returned in text and appended to the data variable then returned 'data'.
    """
    tbody = driver.find_element(By.XPATH, '//*[@id="RsltsGrid"]/div[4]/table/tbody')
    data = []
    for tr in tbody.find_elements(By.XPATH, './/tr'):
        row = [item.text for item in tr.find_elements(By.XPATH, './/td')]
        data.append(row)
    return data

def multiple_pages(driver):
    """
    If target user has more than one page of results. In the current page we extract the data with 'extract_data' function and 
    then click on the 'next' button after 10 seconds. Then extract the content of that page but with 2 variable: 'data' and 'prev_data'
    We compare the next and current page data if both are the same then we know there is no more page so we just break out of the if
    statement and  add the data to 'all_data' --> return data. 
    """
    all_data = []
    prev_data = None
    while True:
        try: 
            data = extract_data(driver)
            if data == prev_data:
                break   # Breaks if clicking 'Next' doesn't lead to new data .
            all_data.extend(data)
            prev_data = data[:]
            next_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="RsltsGrid"]/div[2]/div[2]/a[3]/span')))
            next_button.click()
            time.sleep(10)
        except (NoSuchElementException, TimeoutException):
            break
    return all_data

def replace_empty_with_null(value):
    """
    Function to be used in 'data_to_excel' function for filling empty cells with 'NULL' string.
    """
    if pd.isnull(value) or value == '':
        return 'NULL'
    else:
        return value

def data_to_excel(data, output_file):
    """
    Using pandas we create a framework where we pass the extracted data and columns we named. Then it creates 
    an excel file. In this excel we made some modification --> Notes Below
    """
    df = pd.DataFrame(data, columns=['Cart', 'Searched Name', 'Party Type', 'Related Name', 'Record Date', 
                                     'Book Type', 'Book/Page', 'Instrument #', 'Comments2', 'Case #', 'Consideration', 'Legal', 'Doc Type'])
    df_columnsremoved = df.drop(['Cart', 'Book Type'], axis=1) # Remove the two columns due to empty cells/not beneficial.
    df_replaced = df_columnsremoved.map(replace_empty_with_null) # Mapping the empty cells with 'NULL'. Utilizing the replace_em... function.
    df_replaced.to_excel(output_file, index=False)
    print("Data has been written to:", output_file)

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
        # Getting it from a list of names to a loop for each name
        for target_name in names:
            if not validate_userinput(target_name):
                print(f"Invalid Input: {target_name}... Please ensure names contain only alphabetical characters and spaces!")
                continue
            driver = driver_initalization()
            website_target(driver, 'https://officialrecords.broward.org/AcclaimWeb/search/Disclaimer?st=/AcclaimWeb/search/SearchTypeName')
            conditions_then_searchboxperson(driver, target_name)
            if not validate_searchresults(driver):
                print(f"No search results found for the name: {target_name}! Moving to the next name...")
                continue

            all_data = multiple_pages(driver)
            driver.quit()
            data_to_excel(all_data, f"{target_name.replace(' ','')}_output.xlsx")

        print("Processing completed for all names in the input file.")
        break

if __name__ == "__main__":
    main()

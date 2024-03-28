"""
State: Florida, County: Collier, Type: Collier Clerk/Recorder
Input: Person of Interest 
Output: Person Information --> Party Names, Recorded, Doc Type, Instrument, Book, Page, #Pgs, Desc/Comments, Parcel IDs

NOTE: Prereq: pip install -r requirements.txr
      Have a 'input.xlsx' / excel file for input
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
from selenium.webdriver.common.action_chains import ActionChains # NOTE: Ex. scroll the page to the bottom
import pandas as pd # NOTE: Send collected data into df --> excel
import re # NOTE: Library for search pattern or in this case to validate input
import time


def driver_initialization():
    """
    Initialize an instance for Chrome browser with ChromDriverManager.
    """
    return webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))

def website_target(driver, url):
    # Get the target URL through driver.get
    return driver.get(url)

def validate_user_input(target_name):
    """
    Error handling: If user inputs numbers/symbols/others besides a last and first name --> invalid input will raise alert.
    Using the re: regular expression import. 
    """
    pattern = r'^[a-zA-Z\s]+$'
    # isinstance is added to ensure that the target name passed is a string not an int
    # i added due to error occurring if user added a number value in the input 
    if isinstance(target_name, str) and re.match(pattern, target_name):
        return True
    else:
        return False

def validate_search_results(driver):
    """
    Error handling: Checks if the user result exists or not. If so then continue if not then return False.
    Previously I had the results table element used to see if the results exist. But it didnt work out since the result table
    appeared even if no results found. But there was a data total element when a search was made. Those with no result led to a 0 data total. 
    """
    try:
        # Wait for the element with data-total attribute to be visible
        element = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-total]"))
        )
        data_total = element.get_attribute("data-total")
        if data_total == "0":
            return False
        else:
            return True
    except NoSuchElementException:
        return False



def searchbox_person(driver, name):
    """
    NOTE: There is no one single text box element for name. There is a last name and first name text box element. 
          But the BUsiness Name within the 'Party Name' section displays the same results as if using last name and first name text box element. (Tried multiple times and compared both results.)
          So using the Business Name text box element.
    """
    # Wait for the dropdown button to be clickable
    # XPath expression to select the first element with the specified class name. Due to mix up with a different element.
    dropdown_button_xpath = "(//span[@class='e-input-group-icon e-ddl-icon e-icons e-ddl-disable-icon'])[1]"

    dropdown_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, dropdown_button_xpath)))
    time.sleep(3)
    dropdown_button.click() # Click the dropdown button
    time.sleep(3)
    # Wait for the dropdown options to appear
    dropdown_options = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CLASS_NAME, "e-dropdownlist")))
    # Find and click the desired option (assuming it's visible)
    name1 = 'Basic Property'
    desired_option = dropdown_options.find_element(By.XPATH, f"//li[contains(text(), '{name1}')]")
    desired_option.click()
    time.sleep(10)
    # After selecting the Basic Property checkbox we go to the input element and send the name.
    # Find the input element to input the name
    input_element = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//input[@id='BusinessCORPubBlazor.ViewModels.PartyGroup0']")))
    input_element.clear()  # Clear any existing text
    input_element.send_keys(name + Keys.ENTER)
    time.sleep(15) # NOTE: Anything below 10 seconds results in not loading the data after 10. Due to large amount of data for 'basic property'

def extract_data(driver):
    """
    The results are given in a table body. We find that body and extract through each table row and its table data/data cell. 
    Which is in a for loop and return the data.
    """
    tbody = driver.find_element(By.CLASS_NAME, "k-table-tbody")
    data = []
    for tr in tbody.find_elements(By.XPATH, './/tr'):
        row = [item.text for item in tr.find_elements(By.XPATH, ".//td")]
        data.append(row)
    return data

def click_element(driver, element):
    """
    In conjunction with multiple pages function. When clicking 'next page'.
    """
    try:
        element.click()
    except Exception:
        # If click fails, try scrolling into view and clicking
        ActionChains(driver).move_to_element(element).perform()
        element.click()

def multiple_pages(driver):
    all_data = []
    prev_data = None
    while True:
        try:
            data = extract_data(driver)
            if data == prev_data:
                break
            all_data.extend(data)
            prev_data = data[:]
            #current_page = int(driver.find_element(By.CSS_SELECTOR, ".k-pager-numbers .k-selected").text.strip())
            
            next_page_button = driver.find_element(By.XPATH, "//button[@title='Go to the next page']")
            aria_disabled = next_page_button.get_attribute("aria-disabled")
            
            # Once at the last page. The 'next page' becomes disabled so we know that there are no more pages. Ending it
            if aria_disabled is None or aria_disabled.lower() == "false":
                click_element(driver, next_page_button)
                time.sleep(10)
            else:
                print("No more pages. Exiting...")
                break  # Break the loop if there are no more pages to navigate to
        except (NoSuchElementException, TimeoutException):
            break
    return all_data

def replace_empty_with_null(value):
    """
    In conjunction with the data_to_excel function. Which replaces the empty values with NULL.
    """
    if pd.isnull(value) or value == '':
        return 'NULL'
    else:
        return value

def data_to_excel(data, output_file):
    """
    Using pandas we create a framework where we pass the extracted data and columns we named. Then we drop 2 columns due to no use for the client. And replace the empty
    values with NULL. Then we output the excel with target name. 
    """
    df = pd.DataFrame(data, columns = ['Empty','Party Names', 'Recorded', 'Doc Type', 'Instrument', 'Book', 'Page', '#Pgs', 'Legal Desc/Comments', 'Parcel IDs', 'Checkout'])
    df = df.drop(['Empty', 'Checkout'], axis=1)
    df = df.map(replace_empty_with_null)
    df.to_excel(output_file, index=False)
    print("Data has been written to:", output_file)

def main():
    """
    Main loop where we utilize all functions to do the webscrapping on the website with the target user. 
    """
    while True:
        try:
            file_path = "./input.xlsx"
            file = pd.read_excel(file_path)
            names = file['Name'].tolist()  # Assuming the column name in the Excel file is 'Name'
        except Exception as e:
            print(f"Error reading the input Excel file: {e}")
            continue
        # Getting it from the list of names --> into a loop for each name
        for target_name in names:
            if not validate_user_input(target_name):
                print(f"Invalid Input: {target_name}... Please ensure names contain only alphabetical characters and spaces!")
                continue
            driver = driver_initialization()
            website_target(driver, 'https://cor.collierclerk.com/coraccess/search/document')
            searchbox_person(driver, target_name)
            if not validate_search_results(driver):
                print(f"No search results found for the name: {target_name}! Moving to the next name...")
                continue
        
            all_data = multiple_pages(driver)
            driver.quit()
            data_to_excel(all_data, f"{target_name.replace(' ', '')}_output.xlsx")
        
        print("Processing completed for all names in the input file.")
        break

if __name__ == "__main__":
    main()

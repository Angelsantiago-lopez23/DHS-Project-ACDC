# **** Date: 4/18/24 | Cleaned/Deleted uneccessary code and organized to be more readable. ****
"""

State: Florida ||| County: Collier County ||| Type: Property Appraiser
Input: Person of Interest
                            Single/Property_Summary --> Excel File(Single) / Append if other yield same.
Output: Person Information 
                            Table Results           --> Excel File(Main) 

*** CREATE an input.xlsx that must include a column header named 'Name' and the 'Person of Interest' in the same column and in the format 'LastName FirstName' ***
*** NOTE: No comma between 'LastName FirstName' and spaces before or after the name besides separating 'LastName FirstName'
*** NOTE: Run 'pip install -r requirements.txt' for those wanting to debug/run file

"""
# Libraries Needed
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService # NOTE: To avoid manually downloading binary dep. for browser.
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By # NOTE: Needed for searching elements in html.
from selenium.webdriver.common.keys import Keys # NOTE: Be able to click enter, arrows, etc.
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, UnexpectedAlertPresentException, NoAlertPresentException
import pandas as pd # NOTE: Send collected data into df --> excel
import time
# Imported os for the PropSum data extraction/excel file creation. 
# Will append data from 'PropSum' results from other target_name similar to an existing 'single'excel file or create.
# Rather than overwriting existing data.
import os

# Initializing the Chrome Driver using the ChromeDriverManager to avoid downloading the appropriate Chrome Browser each time.
def driver_initialization():
    return webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))

def webscrape(driver, target_name):
    """
    REVAMPED: 
        Before: Cluttered and difficulty for others to follow and duplication.
        After: Users should be able to follow and readable. While process of webscrapping below. 
    PROCESS EXPLAINED: 
        - driver.get() --> Go to the designated website
        - searchbox() --> After opening the website. We make our way to the user textbox. We must go through the conditions first then be able to pass input. 
        - if not validate() --> Returns True if search table or Property Summary results are being display. Returns False if no results appeared or other errors. 
        - declare the all_data variable 
        - following that data is extracted through multiple_pages() function. --> inside that is an extract() function where main extracted data is happening 
        - lastly return all_data back to main --> pd --> dataframe --> excel
    
    """

    driver.get("https://www.collierappraiser.com/")

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
        columns=['Number','Parcel No.', 'UC.', 'Owner Name', 'No.', 'Street', 'S/C No.', 'Bk/Bd', 'L/Unt', 'Sold', 'Sale Amt', 'Market']

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
            df.drop('Number', axis=1)
            df.map(replace_emptyvalues_with_null)
            df.to_excel('collier_property_appraiser.xlsx', index = False)
        else:
            #print("*** NO DATA AVAILABLE TO SAVE ***") You can uncomment if want displayed. Commented out to be appear cleaner in terminal.
            pass

        print("*** PROCESSING COMPLETED FOR ALL NAMES ***")
        break

    driver.quit()

# ------------ ABOVE: Main loop and the Webscrape Operation -------------- BELOW: The sub function operation that is executed when doing the WebScrape Operation ----

def searchbox(driver, target_name):

    frame_rbottom = WebDriverWait(driver, 5).until(EC.frame_to_be_available_and_switch_to_it("rbottom"))

    try:
        continue_button = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Continue']")))
        continue_button.click()
        time.sleep(5)
    except Exception:
        #print(f"Error Clicking the Continue Condition Button: {e}") Uncomment for debug issues and add 'as e' following Exception
        pass

    driver.switch_to.default_content() # Switch back to default content
    driver.switch_to.frame('logo') # Switch to the logo frame
    driver.switch_to.frame('main') # Then Switch to the main frame 

    try:
        search_database_button = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, '//a[contains(text(), "Search Database")]')))
        search_database_button.click()
        time.sleep(5)
    except Exception as e:
        print(f"Error clicking the Search Database Button: {e}")

    driver.switch_to.default_content() # Back to the default frame
    driver.switch_to.frame('rbottom') # Switch to the rbottom frame

    i_accept_button = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.LINK_TEXT, 'I Accept')))
    i_accept_button.click()
    time.sleep(5)

    try:
        input_element = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, 'Name1')))
        input_element.click() # Click the textbox 
        time.sleep(3)
        
        if ' ' in target_name:
            last_name, first_name = target_name.split()
            target_name = last_name + ",  " + first_name
        else:
            pass
        input_element.send_keys(str(target_name) + Keys.ENTER)
        time.sleep(10)

    except Exception as e:
        print(f"Error occured while searching: {e}")
        
def validate(driver, wait_time=60):

    try:
        for _ in range(wait_time):
            try:
                result_table = driver.find_element(By.CLASS_NAME, "ui-jqgrid-btable")
                if result_table:
                    return True
                
            except NoSuchElementException:
                pass

            try:
                prop_sum = driver.find_element(By.ID, "PropSum")
                if prop_sum:
                    return True
                
            except NoSuchElementException:
                pass

    except UnexpectedAlertPresentException:
        return False

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

            next_page_button = driver.find_element(By.XPATH, "//td[@id='next_pager']")
            class_attribute = next_page_button.get_attribute("class")

            if "ui-state-disabled" not in class_attribute:
                next_page_button.click()
                time.sleep(10)  # Add a short delay to allow the page to load
            
            else:
                print("No more pages. Exiting...")
                break  # Break the loop if the "Next" page button is disabled

    except (NoSuchElementException, TimeoutException) as e:
        #print(f"Error occurred with changing pages: {e}") Uncomment for debugging. 
        pass

    return all_data

def extract_data(driver):

    data = []

    try:
        # If table results appears then extract from table. 
        if driver.find_elements(By.CLASS_NAME, 'ui-jqgrid-btable'):
            tbody = driver.find_element(By.CLASS_NAME, 'ui-jqgrid-btable')
            for tr in tbody.find_elements(By.XPATH, './/tr'):
                row = [item.text for item in tr.find_elements(By.XPATH, ".//td")]
                data.append(row)
        
        # If single result appear/Property Summary page then extract from approp. tables.
        # And data extracted will be put in Dataframe --> Excel here since its just a page. 
        elif driver.find_elements(By.ID, 'PropSum'):
            prop_summary = driver.find_element(By.ID, 'PropSum')
            data_variant = []
            # Extract data from tables within the property summary
            tables = prop_summary.find_elements(By.XPATH, ".//table")
            # Iterate over the first 4 tables
            for table in tables[:4]:
                # Iterate over each row in the table
                for tr in table.find_elements(By.XPATH, ".//tr"):
                    # Extract the text of each cell in the row
                    row_data = [td.text.strip() for td in tr.find_elements(By.XPATH, ".//td")]
                    # Store data in the list
                    data_variant.extend(row_data)
            data_dict = {data_variant[i]: data_variant[i+1] for i in range(0, len(data_variant), 2)}
            df_2 = pd.DataFrame(data_dict.items(), columns=['Name', 'Value'])

            # Specify the path to the output Excel file
            output_file_path = "collier_property_appraiser_single_result.xlsx"

            # Check if the output file already exists
            if os.path.exists(output_file_path):
                existing_df = pd.read_excel(output_file_path)
                existing_df = pd.concat([existing_df, df_2], ignore_index=True)
                existing_df.to_excel(output_file_path, index = False)
            else:
                df_2.to_excel(output_file_path, index = False)
        
        else:
            pass
        
    except Exception as e: 
        print(f"Error occurred during data extraction: {e}")

    return data

def replace_emptyvalues_with_null(value):
    if pd.isnull(value) or value == '':
        return 'NULL'
    else:
        return value


if __name__ == "__main__":
    main()



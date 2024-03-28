"""
State: Florida, County: Collier, Type: Collier Property/Appraiser
Input: Person of Interest: 
Output: NOTE 2 different output:
        1. Person Information (Single Data Result) --> Property Summary (ParcelNo/SiteAddress/City/Zone, Name&Address/City/State/Zip, MapNo/StrapNo/Section/Township
                                                                         /Range/Acres, and Legal)
        2. Person Information (More than ONE Data Result) --> Number, Parcel No, UC, Owner Name, No., Street, S/C No., Bk/Bd, L/Unt,
                                                              Sold, Sale Amt, Market

Note: Prereq: pip install -r requirements.txt
      have a 'input.xlsx' / excel file for input 
"""

# Libraries Needed 
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService # NOTE: To avoid manually downloading binary dep. for browser.
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By # NOTE: Needed for searching elements in html.
from selenium.webdriver.common.keys import Keys # NOTE: Be able to click enter, arrows, etc.
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, UnexpectedAlertPresentException, NoAlertPresentException
from selenium.webdriver.common.action_chains import ActionChains # NOTE: Ex. scroll the page to the bottom
import pandas as pd # NOTE: Send collected data into df --> excel
import re # NOTE: Library for search pattern or in this case to validate input
import time

def driver_initialization():
    # Initialize an instance for Chrome Browser with ChromeDriverManager
    return webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))

def website_target(driver, url):
    return driver.get(url) # Get the target URL 

def validate_user_input(target_name):
    """
    Error Handling: If user inputs numbers/symbols/others besides a last and first name --> invalid input will raise alert
    Using the re: regular expression import  
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
    Error Handling: Checks if the user results exist or not. If so then continue if not then return False. 
                    We will be checking 2 different result table. Since a different element appears if only one result was found. 
                    Which is a summary of that data but if more than one result it will result in a result table.    
                    Now if we dont find either. It will display 'no parcel found' which appears as a pop up alert.               
    """
    try:
        single_result = driver.find_element(By.CLASS_NAME, 'ui-jqgrid-btable')
        result_table = driver.find_element(By.ID, 'PropSum')
        if single_result:
            time.sleep(5)
            return True
        elif result_table:
            time.sleep(5)
            return True
        else:
            return False
    except NoSuchElementException:
        print("No search results found.")
        return False
    except (UnexpectedAlertPresentException, NoAlertPresentException) as e:
        print("An unexpected alert occurred: No Parcels Found")
        #print(e) # Uncomment to see what error exactly occured.
        return False



       
    
def searchbox_person(driver, name):
    """
    Before we are able to reach the search box. We must accept the:
        Privacy Policy(Continue) --> Search Database(Find and Click) --> Disclaimer(Click I Accept Button) --> Owner Textbox 
    NOTE: Issue I had was each pop up or page was in different frames. And some frames couldn't be access directly, had to move through
          the frame structure to that certain frame.
    
    After all the conditions, we are able to send the target name.
    """
    # Wait for the frame 'rbottom' to be available and click
    frame_rbottom = WebDriverWait(driver, 10).until(EC.frame_to_be_available_and_switch_to_it('rbottom'))
    # Now able to click on the continue button that is in the rbottom frame 
    try:
        continue_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div[3]/div/button')))
        continue_button.click()
        time.sleep(5)
    except Exception as e:
        print('Error Clicking the continue condition button:', str(e))
    driver.switch_to.default_content() # Switch back to default content
    driver.switch_to.frame('logo') # Switch to the logo frame
    driver.switch_to.frame('main') # Then Switch to the main frame 
    # Now inside the main frame, find and click the 'search database' button
    try: 
        search_database_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//a[contains(text(), "Search Database")]')))
        search_database_button.click()
        time.sleep(5)
    except Exception as e:
        print('Error clicking the database search button', str(e))
    driver.switch_to.default_content() # Back to the default frame
    driver.switch_to.frame('rbottom') # Switch to the rbottom frame
    time.sleep(5)
    # After switching back to rbottom frame. We must click 'I Acccept Button'. Another condition before actual sending target name.
    iaccept_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.LINK_TEXT, 'I Accept')))
    iaccept_button.click()
    time.sleep(5)
    # Setting up the input element to pass the target name to the textbox
    input_element = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, 'Name1')))
    try:
        input_element.click() # Click the textbox 
        time.sleep(3)
    except:
        pass
    last_name, first_name = name.split() # Splitting the name to include a comma after the last name
    name = last_name + ", " + first_name # Due to excel simply having last and first name in data cell. And it needs a comma for results to appear.
    input_element.send_keys(name + Keys.ENTER)
    time.sleep(10)

def extract_data(driver):
    """
    To extract data from the results of the target name.
    There are two results: Single Result and Multiple Result table. 
    If only one result appears then we will be presented a in depth information but if more than one 
    data result appears then we are presented a table body with summaries. 
    """
    #data = []
    # Check if there are multiple results
    if len(driver.find_elements(By.CLASS_NAME, 'ui-jqgrid-btable')) > 0:
        # If there are multiple results, extract data from the table
        tbody = driver.find_element(By.CLASS_NAME, 'ui-jqgrid-btable')
        data = []
        for tr in tbody.find_elements(By.XPATH, './/tr'):
            row = [item.text for item in tr.find_elements(By.XPATH, ".//td")]
            data.append(row)
        return data
        #df = pd.DataFrame(data, columns=['Number', 'Parcel No.', 'UC.', 'Owner Name', 'No.', 'Street', 'S/C No.', 'Bk/Bd', 'L/Unt', 'Sold', 'Sale Amt', 'Market'])
        #df.to_excel("output.xlsx")
    else:
        # If there's just one result, extract data from the property summary
        prop_summary = driver.find_element(By.ID, 'PropSum')
        data_list = []
        # Extract data from tables within the property summary
        tables = prop_summary.find_elements(By.XPATH, ".//table")
        # Iterate over the first 4 tables
        for table in tables[:4]:
            # Iterate over each row in the table
            for tr in table.find_elements(By.XPATH, ".//tr"):
                # Extract the text of each cell in the row
                row_data = [td.text.strip() for td in tr.find_elements(By.XPATH, ".//td")]
                # Store data in the list
                data_list.extend(row_data)
        data_dict = {data_list[i]: data_list[i+1] for i in range(0, len(data_list), 2)}
        df = pd.DataFrame(data_dict.items(), columns=['Name', 'Value'])
        output_file = "collier_propertyappraiser_singleresult_data.xlsx"
        df.to_excel(output_file, index=False)
        print("Data has been written to:", output_file)
        """
         Had issues with datatoexcel for this result table when using the function below. Couldn't distinguish
        between the 2 since it yield different results. So I decided to do it here since its just one result/no more pages. 
        And since the result is not displayed corretly in a mess so it decided to put in columns of name and value. And convert to excel and quit driver. 
        """
        driver.quit()
        


def multiple_pages(driver):
    """
    We are extracting data using the next page button. Since there are more than one results of page. 
    The extraction of data stops when the button is disabled. From there we know no more data is to be extracted so we 
    break and return all collected data. 
    """
    all_data = []
    prev_data = None
    while True:
        try:
            data = extract_data(driver)
            if data == prev_data:
                break
            all_data.extend(data)
            prev_data = data[:]
            
            next_page_button = driver.find_element(By.XPATH, "//td[@id='next_pager']")
            class_attribute = next_page_button.get_attribute("class")
            
            # Check if the "Next" page button is disabled
            if "ui-state-disabled" not in class_attribute:
                next_page_button.click()
                time.sleep(10)  # Add a short delay to allow the page to load
            else:
                print("No more pages. Exiting...")
                break  # Break the loop if the "Next" page button is disabled
        except (NoSuchElementException, TimeoutException):
            break
    return all_data

def replace_empty_with_null(value):
    if pd.isnull(value) or value == '':
        return 'NULL'
    else:
        return value

def data_to_excel(data, output_file):
    if data:  # Check if data is not empty
        # Extracted data is in a different format (adjust as needed)
            # Example: Create DataFrame with no specified column names
            df = pd.DataFrame(data)
            df = pd.DataFrame(data, columns = ['Number','Parcel No.', 'UC.', 'Owner Name', 'No.', 'Street', 'S/C No.', 'Bk/Bd', 'L/Unt', 'Sold', 'Sale Amt', 'Market'])
            df.drop('Number', axis=1)
            df.map(replace_empty_with_null)
            df.to_excel(output_file, index=False)
            print("Data has been written to:", output_file)
    else:
        print("No data to write.")

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
            website_target(driver, 'https://www.collierappraiser.com/')
            searchbox_person(driver, target_name)
            if validate_search_results(driver):
                print(f"No search results found for the name: {target_name}! Moving to the next name...")
                driver.quit()
                continue
        
            all_data = multiple_pages(driver)
            driver.quit()
            data_to_excel(all_data, f"{target_name.replace(' ', '')}_output.xlsx")
        
        print("Processing completed for all names in the input file.")
        break

if __name__ == "__main__":
    main()

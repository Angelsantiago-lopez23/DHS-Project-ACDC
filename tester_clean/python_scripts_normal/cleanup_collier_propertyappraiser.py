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


def driver_initialization():
    return webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))



def webscrape(driver, target_name):

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
            file_path = "./input2.xlsx"
            file = pd.read_excel(file_path)
            names = file['Name'].tolist()
            all_data = []
        except Exception as e:    
            print(f"Error reading the input Excel file: {e}")

        for target_name in names:

            data = webscrape(driver, target_name)
            all_data.extend(data)

        df = pd.DataFrame(all_data, columns=columns)
        df.to_excel('collier_property_appraiser.xlsx', index = False)

        print("*** PROCESSING COMPLETED FOR ALL NAMES ***")
        break

    driver.quit()



def searchbox(driver, target_name):

    frame_rbottom = WebDriverWait(driver, 10).until(EC.frame_to_be_available_and_switch_to_it("rbottom"))

    try:
        continue_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Continue']")))
        continue_button.click()
        time.sleep(5)
    except Exception as e:
        print(f"Error clicking the Continue Condition button: {e}")

    driver.switch_to.default_content() # Switch back to default content
    driver.switch_to.frame('logo') # Switch to the logo frame
    driver.switch_to.frame('main') # Then Switch to the main frame 

    try: 
        search_database_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//a[contains(text(), "Search Database")]')))
        search_database_button.click()
        time.sleep(10)
    except Exception as e:
        print(f"Error clicking the Search Database button: {e}")
    
    driver.switch_to.default_content() # Back to the default frame
    driver.switch_to.frame('rbottom') # Switch to the rbottom frame
    time.sleep(5)

    i_accept_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.LINK_TEXT, 'I Accept')))
    i_accept_button.click()
    time.sleep(5)

    try:
        input_element = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, 'Name1')))
        input_element.click() # Click the textbox 
        time.sleep(3)
        
        if ' ' in target_name:
            last_name, first_name = target_name.split()
            target_name = last_name + ",  " + first_name
        else:
            pass

        #last_name, first_name = target_name.split()
        #target_name = last_name + ",  " + first_name
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
    previous_data = None

    try:
        while True:
            new_data = extract_data(driver)
            if new_data == previous_data:
                break
            all_data.extend(new_data)
            previous_data = new_data[:]

            next_page_button = driver.find_element(By.XPATH, "//td[@id='next_pager']")
            class_attribute = next_page_button.get_attribute("class")

            #if new_data == previous_data:
                #break

            if "ui-state-disabled" not in class_attribute:
                next_page_button.click()
                time.sleep(10)  # Add a short delay to allow the page to load
            
            else:
                print("No more pages. Exiting...")
                break  # Break the loop if the "Next" page button is disabled

    except (NoSuchElementException, TimeoutException) as e:
        print(f"Error occurred with changing pages: {e}")

    return all_data



def extract_data(driver):

    data = []

    try:
        if WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "ui-jqgrid-btable"))):
            # If there are multiple results, extract data from the table
            tbody = driver.find_element(By.CLASS_NAME, 'ui-jqgrid-btable')
            #data = []
            for tr in tbody.find_elements(By.XPATH, './/tr'):
                row = [item.text for item in tr.find_elements(By.XPATH, ".//td")]
                data.append(row)
            #return data
        
        elif WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "PropSum"))):
            data_variant = []
            prop_summary = driver.find_element(By.ID, 'PropSum')
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
            df = pd.DataFrame(data_dict.items(), columns=['Name', 'Value'])
            df.to_excel("collier_property_appraiser_single_result", index = False)
            print("i passed here")
            #return data
        
        else:
            pass
        
    except Exception as e: 
        print(f"Error occurred during data extraction: {e}")

    return data




    











if __name__ == "__main__":
    main()




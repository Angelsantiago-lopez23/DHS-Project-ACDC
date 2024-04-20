# **** Date: 4/19/24 | Cleaned/Deleted uneccessary code and organized to be more readable. ****
"""
State: Florida ||| County: Collier County ||| Type: Clerk/Recorder
Input: Person of Interest
Output: Person Information --> Download Excel File --> Save Data into another Excel File --> Delete Downloaded File --> Start Process Again & Append to the designated Excel file until done

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
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import pandas as pd # NOTE: Send collected data into df --> excel
import time
import os # To delete downloaded excel file and append data to new excel file
from selenium.webdriver.chrome.options import Options

# Initializing the Chrome Driver using the ChromeDriverManager to avoid downloading the appropriate Chrome Browser each time.
def driver_initialization():
    # Chrome options used to set download to default directory
    chrome_options = Options()
    chrome_options.add_experimental_option("prefs", {
                "download.default_directory": os.getcwd(),
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True
            })
    return webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)

def webscrape(driver, target_name):
    """
    REVAMPED: 
        Before: Unorganized process and duplication of code.
        After: Users should be able to follow the whole process of webscrapping (down below)
    PROCESS EXPLAINED: 
        - Driver.get() --> Go to designated website. 
        - searchbox() --> Click reset to remove any preset/name before --> Select the 'Property Type' documents --> Click on textbox and pass target name --> let results load
        - store acqurired data in data variable and acquired data is done through validate(driver)
            - through a try and except block where the 'try' checks for the excel button. if so downloads the file and read the excel file where it is stored in a df then removes the downloaded file 
                - removed since multiple downloads of different target cause errors due to name file conflict. after it returns that data 
            - if no excel button then the except is executed where nothing is returned. process start again with next name 
        - in the end return data back to main loop
        - if there is data then appended to the all_data variable and once process done with all target_names, the collected data is concated in a dataframe --> replace empty values with null --> to excel --> done
    """

    driver.get("https://cor.collierclerk.com/coraccess/search/document")

    searchbox(driver, target_name)

    data = validate(driver)

    return data


def main():

    driver = driver_initialization()
    driver.maximize_window()

    try:
        file_path = "./input.xlsx"
        file = pd.read_excel(file_path)
        names = file['Name'].tolist()
    except Exception as e:
        print(f"Error reading the input Excel file: {e}")
        driver.quit()
        return 

    all_data = []

    for target_name in names:
        data = webscrape(driver, target_name)

        if data is not None:
            all_data.append(data)

    if all_data:
        final_data = pd.concat(all_data)
        final_data = replace_emptyvalues_with_null(final_data)
        final_data.to_excel("collier_clerk_recorder.xlsx", index=False)
    
    print("*** PROCESSING COMPLETED FOR ALL NAMES ***")

    driver.quit()

# ------------ ABOVE: Main loop and the Webscrape Operation -------------- BELOW: The sub function operation that is executed when doing the WebScrape Operation ----

def searchbox(driver, target_name):

    time.sleep(3)
    clear_results_button = driver.find_element(By.XPATH, "//button[text()='Reset']")
    clear_results_button.click()
    time.sleep(3)

    try:
        document_presets_dropdown = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, "//span[@class='e-ddl e-lib valid e-input-group e-control-container e-control-wrapper e-valid-input']")))
        document_presets_dropdown.click()
        time.sleep(3)
        document_presets_dropdown.send_keys(Keys.ARROW_DOWN)
        time.sleep(2)
        document_presets_dropdown.send_keys(Keys.ENTER)
        time.sleep(1)
    except Exception:
        #print("Error occurred when selecting dropdown pre-sets! Search Results still possible!")
        pass

    try:
        business_name_textbox = driver.find_element(By.XPATH, "//input[@id='BusinessCORPubBlazor.ViewModels.PartyGroup0']")
        business_name_textbox.click()
        business_name_textbox.clear()
        time.sleep(2)
        business_name_textbox.send_keys(str(target_name) + Keys.ENTER)
        time.sleep(15)
    except Exception as e:
        print(f"Error occurred while searching: {e}")


def validate(driver, wait_time=10):

    try:
        # Check if the export button is clickable
        download_excel_button = WebDriverWait(driver, wait_time).until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Export to Excel']")))
        download_excel_button.click()
        time.sleep(2)  # Assuming it takes some time to download
        # Extract data from the downloaded file
        download_file_path = "./OfficialRecordsSearch.xlsx"

        if os.path.exists(download_file_path):
            existing_df = pd.read_excel(download_file_path)
            # Modify the existing_df as needed
            os.remove(download_file_path)  # Delete the file after reading its content
            return existing_df
        else:
            return None
        
    except (TimeoutException, NoSuchElementException) as e:
        #print(f"Error while downloading Excel file: {e}") Uncomment for debug issues. 
        return None
    
def replace_emptyvalues_with_null(df):
    return df.map(lambda x: 'NULL' if pd.isnull(x) or x in ['', ' ', None, 'NaN', 'N/A', 'NA'] else x)


if __name__ == "__main__":
    main()

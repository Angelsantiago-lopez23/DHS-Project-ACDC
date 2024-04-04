"""
State: Florida, County: Coller, Type: Collier Clerk/Recorder
Input: Person of Interest
Output: Person Information -> Party Names, Recorded, Doc Type, Instrument, Book, #Pgs, Desc/Comments, Parcel IDS

NOTE: Prereq: pip install -r requirements.txt
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
import pandas as pd # NOTE: Send collected data into df --> excel
import re # NOTE: Library for search pattern or in this case to validate input
import time
import os 
from selenium.webdriver.chrome.options import Options

# Function thats checks the target name are valid 'names format'
def validate_user_input(target_name):

    pattern = r'^[a-zA-Z\s]+$'
    if isinstance(target_name, str) and re.match(pattern, target_name):
        return True
    else:
        print(f"Invalid Input: {target_name}...Please double check names to only contain alphabetical characters and spaces!")
        return False
# Function that replaces empty cells with 'NULL' value    
def replace_empty_wnull(value):
    if pd.isnull(value) or value == '':
        return 'NULL'
    else:
        return value
    
def main():

    while True:
        try:
            file_path_input = "./input.xlsx"
            file = pd.read_excel(file_path_input)
            names = file['Name'].tolist()
        except Exception as e:
            print(f"Error reading the input Excel file: {e}")
            break

        for target_name in names:
            if not validate_user_input(target_name):
                continue
            # Setting the driver ready and downloads set to default directory
            chrome_options = Options()
            chrome_options.add_experimental_option("prefs", {
                "download.default_directory": os.getcwd(),
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True
            })
            driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
            driver.get('https://cor.collierclerk.com/coraccess/search/document')
            # Waiting for the presets to appear. Then sending keys to select the correct document type.
            time.sleep(5)
            document_presets_dropdown = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, "//span[@class='e-ddl e-lib valid e-input-group e-control-container e-control-wrapper e-valid-input']")))
            document_presets_dropdown.click()
            time.sleep(5)
            document_presets_dropdown.send_keys(Keys.ARROW_DOWN)
            time.sleep(5)
            document_presets_dropdown.send_keys(Keys.ENTER)
            time.sleep(5)
            # After correct presets. We must click on textbox('Business Name') and pass names
            business_name_textbox = driver.find_element(By.XPATH, "//input[@id='BusinessCORPubBlazor.ViewModels.PartyGroup0']")
            business_name_textbox.click()
            business_name_textbox.send_keys(target_name + Keys.ENTER)
            time.sleep(15) # Takes a while for results to load
            # Try and Except if the Excel button appears. Except occurs when no button appears and leads to ending of session.
            try:
                download_excel_button = driver.find_element(By.XPATH, "//span[text()='Export to Excel']")
                download_excel_button.click()
                time.sleep(5)
                # Current directory is where the file is downloaded. 
                downloaded_file_path = "./OfficialRecordsSearch.xlsx"
                # Construct new file name based on target name
                new_file_name = f"{target_name.replace(' ', '')}_output.xlsx"
                # Rename the downloaded file to match the new file name
                os.rename(downloaded_file_path, new_file_name)
                print(f"File downloaded and renamed to {new_file_name}")
                # Read the downloaded Excel file into a DataFrame
                df = pd.read_excel(new_file_name)
                # Apply the replace_empty_wnull function using .map()
                df = df.map(replace_empty_wnull)
                # Write the DataFrame back to Excel
                df.to_excel(new_file_name, index=False)
                
            except NoSuchElementException:
                print(f"No Export to Excel found therefore no results appeared for {target_name}")
                
            driver.quit()
        
        print("Processing completed for all names in the input file!")
        break

if __name__ == "__main__":
    main()
            




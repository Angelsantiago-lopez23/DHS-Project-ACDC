"""
State: Florida, County: Broward, Type: Property Appraiser
Input: Person of interest 
Output: Person information --> Folio Number, Owner Name, Street Address --> EXCEL

NOTE: Prereq: pip install -r requirements.txt
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
    Initialize an instance for Chrome browser. With ChromeDriverManager.
    """
    return webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))

def website_target(driver, url):
    """
    Get the target url through driver.
    """
    driver.get(url)

def validate_userinput(target_name):
    """
    Error handling: So if user inputs numbers or something other than a first and last name --> invalid input so try again until satisfied.
    Using re search pattern.
    """
    pattern = r'^[a-zA-Z\s]+$'
    if re.match(pattern, target_name):
        return True
    return False

def validate_searchresults(driver):
    """
    Error handling: If target user exist then continue if not than return False. 
    """
    try: 
        driver.find_element(By.XPATH, '//*[@id="tbl-list-parcels"]')
        return True
    except NoSuchElementException:
        return False

def searchbox_person(driver, name):
    """
    Have a 10second delay to wait for the element to exist. Helps if the client has slow internet connection or element pops up after a moment.
    Using the expected condition import and time import. 
    Then we send keys and in this case 'enter' to search for the targeted user.
    """
    input_element = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, "form-control")))
    try: 
        input_element.click()
        time.sleep(5)
    except:
        pass
    input_element.send_keys(name + Keys.ENTER)
    time.sleep(5)

def extract_data(driver):
    """
    The results are given in a table so we highlight the table element. 
    From there a for loop for each row. --> Then each table cell is returned in text and appended to the data variable. 
    Then returned. 
    """
    tbody = driver.find_element(By.XPATH, '//*[@id="tbl-list-parcels"]/tbody')
    data = []
    for tr in tbody.find_elements(By.XPATH, './/tr'):
        row = [item.text for item in tr.find_elements(By.XPATH, './/td')]
        data.append(row)
    return data

def multiple_pages(driver):
    """
    We know target user will have one page or more of results. In a while loop we compare each page data with each other. If a page of results is similar to 
    the previous page then we know that is the last page of results. 
        - NOTE: I tried pagnation but that didn't work and the page numbers but it rose errors so I took this approach. 
    After the last page we return all the data from all pages. 
    """
    all_data = []
    prev_data = None
    while True:
        try:
            data = extract_data(driver)
            if data == prev_data:
                break  # Exit the loop if clicking "Next" doesn't lead to new data
            all_data.extend(data)
            prev_data = data[:]
            next_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="btnNextRecords"]')))
            next_button.click()
            time.sleep(10)  # Adjust sleep time as needed
        except (NoSuchElementException, TimeoutException):
            break
    return all_data

def data_to_excel(data, output_file):
    """
    Using pandas we create a datafram where we pass the data extracted and create a excel file with predetermined named column: "Folio, Name, and Address". 
    Which is then converted to an excel file. 
    """
    df = pd.DataFrame(data, columns = ['Folio', 'Name', 'Address'])
    df.to_excel(output_file, index = False)
    print("Data has been written to:", output_file)

def main():
    """
    Main loop where user is asked the targeted name and from there the sequence of function executes/webscrapper. 
    """
    while True:
        target_name = input("Enter the name to search(First Name Last Name): ")
        if not validate_userinput(target_name):
            print("Invalid Input...Please enter only alphabetical characters/spaces!")
            continue
        driver = driver_initalization()
        website_target(driver, 'https://web.bcpa.net/BcpaClient/#/Record-Search')
        searchbox_person(driver, target_name)

        if not validate_searchresults(driver):
            print("No search result found for the targeted name! Please try again!")
            driver.quit()
            continue
        all_data = multiple_pages(driver)
        driver.quit()
        data_to_excel(all_data, f"{target_name.replace(' ', '')}_output.xlsx")
        break

    #target_name = input("Enter the name to search(First Name Last Name): ")
    #driver = driver_initalization()
    #website_target(driver, 'https://web.bcpa.net/BcpaClient/#/Record-Search')
    #searchbox_person(driver, target_name)
    #all_data = multiple_pages(driver)
    #driver.quit()
    #data_to_excel(all_data, f"{target_name.replace(' ', '')}_output.xlsx")


if __name__ == "__main__":
    main()

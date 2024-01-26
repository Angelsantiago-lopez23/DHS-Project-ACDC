# Import necessary libraries and modules for web scraping and data handling
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time

def wait_for_element(driver, locator, wait_time=30):
    """
    Waits for a web element to be clickable based on a provided locator.
    :param driver: WebDriver instance
    :param locator: Tuple containing locator strategy and locator value
    :param wait_time: Maximum time to wait for the element
    :return: WebElement that is clickable
    """
    return WebDriverWait(driver, wait_time).until(EC.element_to_be_clickable(locator))

def validate(driver, wait_time=60):
    """
    Validates if the search results are available or if there are no matches.
    :param driver: WebDriver instance
    :param wait_time: Maximum time to attempt validation
    :return: Boolean indicating if search results are valid or not
    """
    for _ in range(wait_time):
        try:
            # Checking for 'No matches found' message
            no_matches_id = 'ctl00_BodyContentPlaceHolder_WebTab1_tmpl0_ErrorLabel'
            no_matches = WebDriverWait(driver, 0.5).until(EC.presence_of_element_located((By.ID, no_matches_id)))
            if "No matches found for given criteria" in no_matches.text:
                return False
        except Exception:
            pass

        try:
            # Checking for the presence of the results table
            results_class = 'resultsDataGrid'
            WebDriverWait(driver, 0.5).until(EC.presence_of_element_located((By.CLASS_NAME, results_class)))
            return True
        except Exception:
            pass
    return False

def extract_table_data(driver, user_input):
    """
    Extracts data from the search results table.
    :param driver: WebDriver instance
    :param user_input: User input string used for the search
    :return: List of extracted data rows
    """
    table = wait_for_element(driver, (By.CLASS_NAME, 'resultsDataGrid'))
    rows = table.find_elements(By.TAG_NAME, 'tr')
    data = []

    for row in rows:
        cols = row.find_elements(By.TAG_NAME, 'td')
        if cols:
            # Extracting various data fields from the table
            strap_folio = cols[0].text
            owner_info = cols[1]
            bold_elements = owner_info.find_elements(By.XPATH, ".//div[@class='bold']")
            bold_text = [elem.text.strip() for elem in bold_elements]
            owner_names = ' '.join(bold_text)

            owner_address = owner_info.text
            for owner_name in bold_text:
                owner_address = owner_address.replace(owner_name, '').strip()

            strap, folio = strap_folio.split('\n', 1)
            site_property_column = cols[2]
            divs = site_property_column.find_elements(By.CLASS_NAME, 'itemAddAndLegal')
            site_address = divs[0].text
            property_description = divs[1].text

            data.append([user_input, strap, folio, owner_names, owner_address, site_address, property_description])

    return data

def navigate_to_next_page(driver, old_table_text):
    """
    Navigates to the next page of search results if available.
    :param driver: WebDriver instance
    :param old_table_text: Text content of the current results table
    :return: Boolean indicating if navigation was successful
    """
    try:
        # Locating the page number dropdown and selecting the next page
        xpath = "//*[substring(@id, string-length(@id) - string-length('_pagenumberList') + 1) = '_pagenumberList']"
        select_element = wait_for_element(driver, (By.XPATH, xpath))
        select = Select(select_element)
        next_value = int(select.first_selected_option.get_attribute("value")) + 1
        select.select_by_value(str(next_value))

        end_time = time.time() + 60
        while True:
            try:
                new_table_text = driver.find_element(By.CLASS_NAME, 'resultsDataGrid').text
                if new_table_text != old_table_text:
                    return True
            except StaleElementReferenceException:
                if time.time() > end_time:
                    return False
                continue
            time.sleep(0.5)
    except NoSuchElementException:
        return False

def initialize_driver():
    """
    Initializes and returns a Selenium WebDriver instance.
    :return: WebDriver instance
    """
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service)

def webscrape(driver, user_input):
    """
    Performs the web scraping task using the provided WebDriver and user input.
    :param driver: WebDriver instance
    :param user_input: User input for search criteria
    :return: List of scraped data
    """
    # Navigating to the website and performing the search
    driver.get("https://www.leepa.org/Search/PropertySearch.aspx")
    name_field = wait_for_element(driver, (By.ID, 'ctl00_BodyContentPlaceHolder_WebTab1_tmpl0_OwnerNameTextBox'))
    name_field.send_keys(user_input)

    search_button = wait_for_element(driver, (By.ID, 'ctl00_BodyContentPlaceHolder_WebTab1_tmpl0_SubmitPropertySearch'))
    search_button.click()

    if not validate(driver):
        return []

    all_data = []
    while True:
        new_data = extract_table_data(driver, user_input)
        all_data += new_data
        table_text = driver.find_element(By.CLASS_NAME, 'resultsDataGrid').text
        if not navigate_to_next_page(driver, table_text):
            break

    return all_data

def main():
    """
    Main function to execute the web scraping process.
    """
    driver = initialize_driver()
    file = pd.read_excel('./input.xlsx')
    names = file['name'].tolist()
    all_data = []

    for name in names:
        data = webscrape(driver, name)
        all_data.extend(data)

    # Creating a DataFrame from the extracted data
    df = pd.DataFrame(all_data, columns=['Name', 'Strap', 'Folio', 'Owners', 'Owners Address', 'Site Address', 'Property Description'])

    # Saving the DataFrame to an Excel file without the index (no additional column of numbers)
    df.to_excel('results.xlsx', index=False)
    driver.quit()

if __name__ == "__main__":
    main()
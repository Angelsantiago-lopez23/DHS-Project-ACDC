# Import necessary libraries and modules for web scraping and data handling
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import urlparse, parse_qs, urlunparse, urlencode
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
    # Breaking down the long text into smaller strings
    part1 = "No bills or accounts matched your search."
    part2 = "Try using different or fewer search terms."
    part3 = "The following tips may also help:"
    full_text = part1 + " " + part2 + " " + part3
    no_results_xpath = f"//p[text()='{full_text}']"

    for _ in range(wait_time):
        try:
            # Checking for 'No matches found' message
            no_results = WebDriverWait(driver, 0.5).until(EC.presence_of_element_located((By.XPATH, no_results_xpath)))
            return False
        except Exception:
            pass

        try:
            # Checking for the presence of the results
            results_class = 'category-search-results'
            WebDriverWait(driver, 0.5).until(EC.presence_of_element_located((By.CLASS_NAME, results_class)))
            return True
        except Exception:
            pass
    return False

def extract_card_data(driver, user_input):
    """
    Extracts data from the search results table.
    :param driver: WebDriver instance
    :param user_input: User input string used for the search
    :return: List of extracted data rows
    """
    div = wait_for_element(driver, (By.CLASS_NAME, 'category-search-results'))
    divs = div.find_elements(By.CLASS_NAME, 'result')
    data = []
    
    for div in divs:
        account = div.find_element(By.CLASS_NAME, 'identifier').text.strip().strip(',')
        account = account.replace('Account', '')
        owners = div.find_element(By.CLASS_NAME, 'name').text.strip().strip(',')

        # Initialize fields with NULL or empty strings
        billing_name_address, owner_address, address = 'NULL', 'NULL', 'NULL'

        address_elements = div.find_elements(By.CLASS_NAME, 'address')

        for address_element in address_elements:
            label = address_element.find_element(By.CLASS_NAME, 'label').text
            address_text = address_element.text.replace(label, '').strip().strip(',')

            if label == "BILLING ADDRESS":
                billing_name_address = address_text
            elif label == "OWNER/ADDRESS":
                owner_address = address_text.replace(owners, '').strip().strip(',')
            elif label == "ADDRESS":
                address = address_text

        data.append([account, owners, owner_address, address, billing_name_address])

    return data


def trying(function, attempts=3, delay=2):
    for _ in range(attempts):
        try:
            result = function()
            return result
        except Exception as e:
            print(f"Attempt failed with error: {e}")
            time.sleep(delay)  # Wait for some time before retrying
    return False

def navigate_to_next_page(driver, current_page_number):
    """
    Navigates to the next page of search results by clicking the pagination button.
    :param driver: WebDriver instance
    :param current_page_number: The current page number
    :return: Boolean indicating if navigation was successful
    """
    try:
        # Find the pagination navigation element
        pagination_nav = wait_for_element(driver, (By.XPATH, "//nav[@aria-label='Pagination']"))
        ul = pagination_nav.find_element(By.TAG_NAME, 'ul')
        list_items = ul.find_elements(By.TAG_NAME, 'li')

        # Finding and clicking the next page button
        for item in list_items:
            if item.text == str(current_page_number + 1):
                item.click()
                return True

        # If the next page button is not found, we might be on the last page
        return False
    except NoSuchElementException:
        # Handle the case where the pagination navigation is not found
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
    driver.get("https://lee.county-taxes.com/public/search/property_tax")
    xpath = "//input[starts-with(@placeholder, 'Enter a name')]"
    name_field = wait_for_element(driver, (By.XPATH, xpath))
    name_field.send_keys(user_input)
    name_field.send_keys(Keys.ENTER)

    if not validate(driver):
        return []

    all_data = []
    current_page_number = 1
    while True:
        new_data = trying(lambda: extract_card_data(driver, user_input), attempts=10, delay=0.5)
        all_data += new_data
        if not navigate_to_next_page(driver, current_page_number):
            break
        else:
            current_page_number += 1
        print('\n\n\n' + 'Iteration Complete' + '\n\n\n')
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
    df = pd.DataFrame(all_data, columns=['Account', 'Owners', 'Owner Address', 'Address', 'Billing Names & Address'])

    # Saving the DataFrame to an Excel file without the index (no additional column of numbers)
    df.to_excel('results.xlsx', index=False)
    driver.quit()

if __name__ == "__main__":
    main()
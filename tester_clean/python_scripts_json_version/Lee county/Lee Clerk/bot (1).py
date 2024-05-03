# Import necessary libraries and modules for web scraping and data handling
import traceback
import random
import pandas as pd
import numpy as np
import re
import time
import os
import requests

# Import undetected_chromedriver
#import undetected_chromedriver as 
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

# Import remaining necessary components from selenium
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, TimeoutException

import whisper

# whisper requirements
ffmpeg_bin_path = r".\ffmpeg-6.1.1-essentials_build\bin"
os.environ["PATH"] += os.pathsep + ffmpeg_bin_path
model = whisper.load_model("base")

# Global variable to track the current mouse position
current_mouse_position = {'x': 0, 'y': 0}

def human_like_type(element, text):
    """
    Types text into a web element in a human-like manner with random delays between keystrokes.
    :param element: The WebElement to type into
    :param text: The text to type
    :return: None
    """
    for character in text:
        element.send_keys(character)
        time.sleep(random.uniform(0.05, 0.2))  # Random delay between keystrokes

def human_like_delay(minimum=0.5, maximum=1.5):
    """
    Generates a random delay duration to mimic human behavior.
    :param minimum: Minimum delay in seconds
    :param maximum: Maximum delay in seconds
    :return: None
    """
    time.sleep(random.uniform(minimum, maximum))

def human_like_scroll(driver, element):
    """
    Scrolls to an element in a human-like manner.
    :param driver: WebDriver instance
    :param element: WebElement to scroll to
    :return: None
    """
    scroll_y_by = element.location['y'] / random.randint(2, 4)
    driver.execute_script(f"window.scrollBy(0, {scroll_y_by});")
    human_like_delay()

def draw_click_marker(driver, x, y):
    """
    Draws a temporary marker on the page to indicate the click position.
    :param driver: WebDriver instance
    :param x: X-coordinate of the click
    :param y: Y-coordinate of the click
    :return: None
    """
    script = f"""
    var body = document.getElementsByTagName('body')[0];
    var div = document.createElement('div');
    div.setAttribute('style', 'position: absolute; left: {x}px; top: {y}px; width: 10px; height: 10px; background-color: red; border-radius: 5px; z-index: 10000;');
    body.appendChild(div);
    setTimeout(function() {{ body.removeChild(div); }}, 1000);
    """
    driver.execute_script(script)

def bezier_curve(start, end, num_of_points=30):
    """
    Generates points along a Bezier curve from start to end.
    :param start: Starting point (x, y)
    :param end: Ending point (x, y)
    :param num_of_points: Number of points to generate along the curve
    :return: List of points along the curve
    """
    # Adjust control points generation to avoid ValueError
    def adjusted_random(start, end):
        low = min(start, end)
        high = max(start, end) + 1  # Ensure high is always greater than low
        return np.random.randint(low, high)

    ctrl_1 = (adjusted_random(start[0], end[0]), adjusted_random(start[1], end[1]))
    ctrl_2 = (adjusted_random(start[0], end[0]), adjusted_random(start[1], end[1]))

    curve_points = []
    for t in np.linspace(0, 1, num_of_points):
        x = (1-t)**3 * start[0] + 3*(1-t)**2 * t * ctrl_1[0] + 3*(1-t) * t**2 * ctrl_2[0] + t**3 * end[0]
        y = (1-t)**3 * start[1] + 3*(1-t)**2 * t * ctrl_1[1] + 3*(1-t) * t**2 * ctrl_2[1] + t**3 * end[1]
        curve_points.append((int(x), int(y)))
    return curve_points


def human_like_click(driver, element):
    global current_mouse_position

    width = element.size['width']
    height = element.size['height']

    # Choose a random position within the element
    x_offset = random.randint(width // 4, width * 3 // 4)
    y_offset = random.randint(height // 4, height * 3 // 4)

    # Calculate absolute click position
    abs_x = element.location['x'] + x_offset
    abs_y = element.location['y'] + y_offset

    # Generate a Bezier curve path from the current mouse position
    path_points = bezier_curve((current_mouse_position['x'], current_mouse_position['y']), (abs_x, abs_y))

    # Draw the path and move through it
    for point in path_points:
        draw_click_marker(driver, *point)
        time.sleep(random.uniform(0.01, 0.05))  # Random delay for realism

    # Update current mouse position
    current_mouse_position = {'x': abs_x, 'y': abs_y}

    # Scroll to the element
    human_like_scroll(driver, element)

    # Execute a JavaScript click at the specific coordinates
    script = f"""
    var evt = new MouseEvent('click', {{
        'view': window,
        'bubbles': true,
        'cancelable': true,
        'clientX': {abs_x},
        'clientY': {abs_y}
    }});
    arguments[0].dispatchEvent(evt);
    """
    driver.execute_script(script, element)

    # Delay to mimic human behavior
    human_like_delay()

def initialize_driver(download_directory):
    """
    Initializes and returns an undetected Selenium WebDriver instance with customized settings.
    
    :param download_directory: The directory where downloads should be saved.
    :return: A Selenium WebDriver instance configured for web scraping.
    """
    # Resolve the relative path to an absolute path
    download_directory = os.path.abspath(download_directory)

    # List of user agents for random selection to mimic different browsers
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36 Edge/18.19582",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.1.2 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36",
        "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0"
    ]

    #options = uc.ChromeOptions()
    options = webdriver.ChromeOptions()

    # Set a random user agent
    options.add_argument(f"user-agent={random.choice(user_agents)}")

    # Preferences for downloading files and handling popups
    prefs = {
        "download.default_directory": download_directory,  # Specify the directory for downloads
        "download.prompt_for_download": False,  # Disable download prompt
        "download.directory_upgrade": True,  # Use the provided directory for downloads
        "safebrowsing.enabled": True,  # Enable safe browsing
        "profile.default_content_setting_values.automatic_downloads": 1,  # Allow automatic downloads
        "profile.default_content_setting_values.popups": 1  # Allow popups
    }
    
    options.add_experimental_option("prefs", prefs)

    # Initialize the undetected ChromeDriver with the specified options
    #driver = uc.Chrome(options=options)
    service = Service(ChromeDriverManager().install())
    
    driver = webdriver.Chrome(service=service, options=options)
    driver.maximize_window()

    return driver


def wait_for_element(driver, locator, wait_time=10):
    """
    Waits for a web element to be clickable based on a provided locator.
    :param driver: WebDriver instance
    :param locator: Tuple containing locator strategy and locator value
    :param wait_time: Maximum time to wait for the element
    :return: WebElement that is clickable
    """
    human_like_delay(0.5, 1.0)
    return WebDriverWait(driver, wait_time).until(EC.element_to_be_clickable(locator))

def good_results(driver, wait_time=60):
    """
    Validates if the search results are available or if there are no matches.
    :param driver: WebDriver instance
    :param wait_time: Maximum time to attempt validation
    :return: Boolean indicating if search results are valid or not
    """

    xpath = "//b[contains(text(), 'Returned') and contains(text(), 'records')]"
    for _ in range(wait_time):
        try:
            results = WebDriverWait(driver, 0.5).until(EC.presence_of_element_located((By.XPATH, xpath)))
            text = results.text
            if "Returned 0 records" in text:
                print('0 records')
                return False  
            elif "records of" in text:
                print("records found")
                return True
            else:
                print("New type of record found please adjust code")
                return False
        except:
            pass

    print("failed to validate returning default false")
    return False


def populate_search_fields(driver, user_input, match_type='Starts With'):
    # Locate the dropdown element, Create a Select object, and Select the option
    dropdown = wait_for_element(driver, (By.ID, 'matchType-Name'))
    select = Select(dropdown)
    select.select_by_visible_text(match_type)

    # Enter the name we are searching for
    name_field = wait_for_element(driver, (By.ID, 'name-Name'))
    name_field.clear()
    human_like_type(name_field, user_input)


def submit_search(driver):
    submit_button = wait_for_element(driver, (By.ID, 'submit-Name'))
    human_like_click(driver, submit_button)


def results_loaded(driver):
    for _ in range(30):  # 30 iterations
        try:
            # Wait up to 0.5 seconds for the download button to be clickable
            WebDriverWait(driver, 0.5).until(EC.element_to_be_clickable((By.ID, "results-Export")))
            print("Export button is present and clickable.")
            return True
        except TimeoutException:
            # If the download button is not found, check the spinner status
            try:
                spinner = driver.find_element(By.XPATH, "//img[@src='/LandMarkWeb/images/AjaxLoad/ajax-loader.blue.gif']")
                if spinner.is_displayed():
                    print("Spinner is displayed, waiting...")
                    # If spinner is displayed, continue to the next iteration
                    continue
                else:
                    # If spinner is present in the DOM but not visible
                    print("Spinner is present but not visible, results might be ready.")
                    return True
            except NoSuchElementException:
                # If the spinner is not found in the DOM at all
                print("Spinner is not present in the DOM, results should be ready.")
                return True
    # If the loop completes without returning, it means the export button was never found
    # and the spinner check condition also did not lead to a return
    print("Timed out waiting for results to be ready.")
    return False


def found_captcha(driver):
    # Switch to reCAPTCHA iframe if it is present
    try:
        iframe = get_iframe_by_title(driver, 'reCAPTCHA')
        if iframe.is_displayed():
            return True
        else:
            return False
    except:
        return False


def get_iframe_by_title(driver, title, printing=False):
    # Find all iframes by their tag name
    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    if printing:
        print(f"\n\nFound {len(iframes)} iframes.")

    # Iterate through all found iframes
    frame = None
    for index, iframe in enumerate(iframes):
        # JavaScript to get all attributes of the element
        js_code = """
        var items = {};
        for (var index = 0; index < arguments[0].attributes.length; ++index) {
            items[arguments[0].attributes[index].name] = arguments[0].attributes[index].value;
        }
        return items;
        """
        # Execute the JavaScript code to get all attributes of the iframe
        attributes = driver.execute_script(js_code, iframe)

        # Conditional printing based on the printing parameter
        if printing:
            print(f"Iframe {index + 1} attributes: {attributes}")

        # Check for a specific title within the retrieved attributes
        iframe_title = attributes.get('title', '')
        if title in iframe_title:
            frame = iframe
            break  # Exit the loop once the matching frame is found
        else:
            if printing:
                print(f"Iframe {index + 1} does not have the specified title or cannot be accessed.")
    return frame


def page_loaded_correctly(driver):
    time.sleep(random.uniform(3.0, 3.5))
    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    print(f"\n\nFound {len(iframes)} iframes.")
    if len(iframes) == 3:
        return True
    else:
        return False 


def complete_audio_captcha(driver):
    # Switch to reCAPTCHA iframe 
    iframe = get_iframe_by_title(driver, 'reCAPTCHA')
    driver.switch_to.frame(iframe)

    # Click the checkbox to trigger the challenge
    checkbox_xpath = "//div[@class='recaptcha-checkbox-border' and @role='presentation']"
    # when checked it looks like this
    # <div class="recaptcha-checkbox-checkmark" role="presentation" style=""></div>
    checkbox = wait_for_element(driver, (By.XPATH, checkbox_xpath))
    checkbox.click()

    driver.switch_to.default_content()
    iframe = get_iframe_by_title(driver, 'recaptcha challenge expires in two minutes')
    driver.switch_to.frame(iframe)

    # Click on the audio challenge button
    audio_button = wait_for_element(driver, (By.ID, "recaptcha-audio-button"))
    audio_button.click()

    # Extract the URL of the audio file
    audio_link = wait_for_element(driver, (By.XPATH, "//a[@title='Alternatively, download audio as MP3']"))
    audio_url = audio_link.get_attribute("href")
    download_audio(audio_url)

    # Convert the audio file to text using whisper 
    result = model.transcribe("audio.mp3", fp16=False)  # transcribe the audio
    text = result["text"]   # extract the text

    cleaned_text = re.sub('[^a-zA-Z0-9]', '', str(text))
    print(cleaned_text)

    # Enter the text in the response field
    response_field = wait_for_element(driver, (By.ID, "audio-response"))
    human_like_type(response_field, cleaned_text)

    # Submit the response
    submit_button = wait_for_element(driver, (By.ID, "recaptcha-verify-button"))
    submit_button.click()

    # Switch back to the main content
    driver.switch_to.default_content()


def download_audio(url):
    """
    Downloads an MP3 file from the specified URL and saves it as 'audio.mp3'
    in the same directory as this script. It overwrites any existing file with the same name.
    It uses a while loop to keep trying until the file has been successfully downloaded
    and is ready for further processing.

    Parameters:
    - url: The URL of the MP3 file to download.
    """
    # The path where the MP3 file will be saved
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'audio.mp3')

    # Check if 'audio.mp3' already exists and inform about the overwrite
    if os.path.exists(file_path):
        print(f"The file {file_path} already exists and will be overwritten.")

    download_successful = False
    while not download_successful:
        print("Attempting to download MP3 file from:", url)
        try:
            response = requests.get(url)
            if response.status_code == 200:
                # Write the content of the response to a file, overwriting if it already exists
                with open(file_path, 'wb') as file:
                    file.write(response.content)
                print("Download attempt complete. Checking file...")
            else:
                print(f"Failed to download file. Status code: {response.status_code}")
                time.sleep(5)  # Wait for 5 seconds before retrying
                continue
        except Exception as e:
            print(f"An error occurred while downloading the file: {e}")
            time.sleep(5)  # Wait for 5 seconds before retrying
            continue

        # Check if the file exists and is not empty
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            print("File has been successfully downloaded and is ready for further processing.")
            download_successful = True
        else:
            print("Downloaded file is not ready. Retrying...")
            time.sleep(5)  # Wait for 5 seconds before retrying


def get_past_main_page(driver):
    # Navigating to the website
    driver.get('https://or.leeclerk.org/LandMarkWeb')

    name_icon = wait_for_element(driver, (By.XPATH, "//*[@alt='Name Search Icon']"))
    human_like_click(driver, name_icon)
    time.sleep(2)

    accept_button = wait_for_element(driver, (By.ID, 'idAcceptYes'))
    human_like_click(driver, accept_button)

def download_file(driver, wait_time=60):
    download_button = wait_for_element(driver, (By.ID, "results-Export"))
    human_like_click(driver, download_button)


def wait_for_file_download(directory, file_start_name):
    while True:
        # List all files in the specified directory
        files = os.listdir(directory)
        
        # Filter files that start with the specified name and have an Excel extension
        matching_files = [file for file in files if file.startswith(file_start_name) and file.endswith('.xlsx')]
        
        if matching_files:
            print(f"File found: {matching_files[0]}")
            break  # Exit the loop if a matching file is found
        
        print("File not found yet. Waiting...")
        time.sleep(2)  # Wait for 5 seconds before checking again


def delete_file(directory, file_start_name):
    files = os.listdir(directory)
    for file in files:
        if file.startswith(file_start_name):
            file_path = os.path.join(directory, file)
            os.remove(file_path)
            print(f"File deleted: {file}")
            return
    print("No matching file found to delete.")


def webscrape(driver, user_input):
    """
    Performs the web scraping task using the provided WebDriver and user input, with retries if results do not load.
    :param driver: WebDriver instance
    :param user_input: User input for search criteria
    :return: True if scraping was successful and file was downloaded, False otherwise.
    """
    
    max_attempts = 5
    for attempt in range(max_attempts):
        if not page_loaded_correctly(driver):
            continue

        populate_search_fields(driver, user_input) 
        
        if found_captcha(driver):
            print(1)
            try:
                complete_audio_captcha(driver)
                print(2)
            except:
                print("did not complete audio captcha or we did not need to")
                driver.switch_to.default_content()
            print(3)

        submit_search(driver)
        time.sleep(random.uniform(1.7, 2.2)) 
        
        if not results_loaded(driver):  
            print(f"Results not loaded, attempt {attempt + 1} of {max_attempts}. Refreshing and retrying...")
            driver.refresh()  
            continue  # Skip the remaining part of the loop and start over
        
        if good_results(driver):  
            download_file(driver)  
            print("File downloaded successfully.")
            driver.refresh() 
            return True
        else:
            return False
    
    # If we reach this point, it means the results never loaded correctly after max attempts
    print("Failed to load results after maximum attempts. Please try again later.")
    return False


def main():
    """
    Main function to execute the web scraping process.
    """
    driver = None
    try:
        all_dfs = []
        download_dir = "./download"  # Adjusted variable name for consistency
        file_name = "_ExportResults"  # This is a part of the file name to look for

        driver = initialize_driver(download_dir)
        file = pd.read_excel('./big_input.xlsx')
        names = file['name'].tolist()

        get_past_main_page(driver)

        columns = ['Search Parameter', 'Status', 'Consideration', 'Search Name', 
                   'Grantor', 'Grantee', 'Record Date', 'Doc Type', 'Book Type', 'Book', 
                   'Page', 'Clerk File Number', 'DocLinks', 'Legal', 'Lot', 'Block', 'Unit', 
                   'Subdivision', 'Building', 'Section', 'Township', 'Range', 'Comment', 'DocLinks']

        for name in names:
            webscraped = webscrape(driver, name)

            if webscraped:
                wait_for_file_download(download_dir, file_name)
                downloaded_files = [f for f in os.listdir(download_dir) if f.startswith(file_name) and f.endswith('.xlsx')]
                if downloaded_files:
                    df = pd.read_excel(os.path.join(download_dir, downloaded_files[0]))
                    # Add missing columns with NULL values
                    for column in columns:
                        if column not in df.columns:
                            df[column] = np.nan
                    # Ensure dataframe has columns in the specified order, adding 'Search Parameter' with the name
                    df = df.reindex(columns=columns, fill_value=np.nan)
                    df['Search Parameter'] = name
                    all_dfs.append(df)
                    # Optionally, delete the file after processing
                    delete_file(download_dir, downloaded_files[0])
            else:
                # Create an empty dataframe with the specified columns, filled with NULLs
                df = pd.DataFrame(columns=columns)
                df.loc[0] = [name] + [None] * (len(columns) - 1)
                all_dfs.append(df)

        # Remove empty or fully NaN DataFrames
        filtered_dfs = [df for df in all_dfs if not df.isnull().all().all()]

        if filtered_dfs:
            final_df = pd.concat(filtered_dfs, ignore_index=True)
        else:
            final_df = pd.DataFrame(columns=columns)

        final_df.to_excel('results.xlsx', index=False)

    except NoSuchElementException as e:
        print(f"Element not found error: {e}")
        print(f"URL at the time of error: {driver.current_url if driver else 'Driver not initialized'}")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        traceback.print_exc()  # Print the full traceback

    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    main()

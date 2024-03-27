from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# Initialize the WebDriver
driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))

# Open the webpage
driver.get("https://www.collierappraiser.com/")

# Wait for the frame with id "rbottom" to be available
frame_rbottom = WebDriverWait(driver, 10).until(EC.frame_to_be_available_and_switch_to_it("rbottom"))

# Find and click the first button on the pop-up
try:
    button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/div[3]/div/button")))
    button.click()
    print("First button clicked successfully!")
except Exception as e:
    print("Error clicking the first button:", str(e))

# Switch to the default content
driver.switch_to.default_content()

# Switch to the parent frame of the "logo" frame
#driver.switch_to.parent_frame()

# Switch to the "logo" frame
driver.switch_to.frame("logo")

# Switch to the "main" frame
driver.switch_to.frame("main")

# Now you're inside the "main" frame, find and click the "Search Database" button
try:
    search_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//a[contains(text(), "Search Database")]')))
    search_button.click()
    print("Second button clicked successfully!")
except Exception as e:
    print("Error clicking the second button:", str(e))

# Close the WebDriver session
time.sleep(10)

# Code above works now I will be clicking the accept conditions 
driver.switch_to.default_content()
driver.switch_to.frame("rbottom")
time.sleep(10)
button_accept = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.LINK_TEXT, "I Accept")))
button_accept.click()
time.sleep(10)



driver.quit()

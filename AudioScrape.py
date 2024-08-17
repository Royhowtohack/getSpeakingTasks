from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import requests
import os
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

# Initialization

URL = input("Please enter the URL for the Speaking Tasks: ")
browser = webdriver.Chrome()
wait = WebDriverWait(browser, 5)
AUDIO_DIRS = ["task1_audios", "task2_audios", "task3_audios", "task4_audios"]

def create_audio_dirs():
    for dir in AUDIO_DIRS:
        if not os.path.exists(dir):
            os.makedirs(dir)

def login():
    LOGIN_URL = 'https://smarter.igo1996.com/teacher/login'
    browser.get(LOGIN_URL)
    # Ensure the page has loaded before executing scripts
    time.sleep(3)
    
    # JavaScript to fill in the phone number and password
    js_fill_script = """
    // Select the phone number input by navigating through specific parents
    document.querySelector('.login-center .form-box input[placeholder="请输入手机号"]').value = '13980612787';
    document.querySelector('.login-center .form-box input[placeholder="请输入手机号"]').dispatchEvent(new Event('input', { bubbles: true }));

    // Select the password input similarly
    document.querySelector('.login-center .form-box input[placeholder="请输入密码"]').value = 'WHeYCPgpKRM4';
    document.querySelector('.login-center .form-box input[placeholder="请输入密码"]').dispatchEvent(new Event('input', { bubbles: true }));
    """
    browser.execute_script(js_fill_script)

    # JavaScript to click each login button
    js_click_script = """
    // Find all login buttons within the same form-box and click each one by one
    let loginButtons = document.querySelectorAll('.login-center .form-box .btn-login');
    loginButtons.forEach((button, index) => {
        console.log(`Clicking button ${index + 1}`);
        button.click();  // Perform a click on each login button

        // Introduce a small delay here to observe the behavior after each click
        new Promise(resolve => setTimeout(resolve, 1000)); // Note: Selenium won't respect this delay, it's just for example
    });
    """
    browser.execute_script(js_click_script)
    # Allow some time after the last click for any actions to complete
    time.sleep(3)

def get_current_page_number():
    """Return the current active page number using different selectors."""
    selectors = [
        '.ivu-page-item.ivu-page-item-active a',  # Original selector
        '.number.active'  # New selector
    ]
    for selector in selectors:
        try:
            active_page_elem = WebDriverWait(browser, 10).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, selector))
            )
            page_number_text = active_page_elem.text.strip()
            return int(page_number_text)
        except (TimeoutException, NoSuchElementException):
            continue  # Try the next selector
    print("Failed to find the active page number element with any known selectors.")
    return None


def process_student():
    time.sleep(3)
    student_name_elem = wait.until(EC.visibility_of_element_located((By.XPATH, '//div[contains(text(),"Name:")]/following-sibling::div[@class="value"]')))
    student_name = student_name_elem.text
    audio_elements = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'audio[src$=".wav"]')))

    if len(audio_elements) != 4:
        raise Exception(f"Expected 4 audio files, but found {len(audio_elements)}")
    
    for i, audio_element in enumerate(audio_elements):
        audio_url = audio_element.get_attribute('src')
        audio_content = requests.get(audio_url).content
        audio_filename = os.path.join(AUDIO_DIRS[i], f"{student_name}_task{i+1}.wav")
        with open(audio_filename, "wb") as f:
            f.write(audio_content)
    
    return student_name  # Return the student's name after processing

def click_on_next_page():
    current_page = get_current_page_number()
    try:
        next_page_num = current_page + 1
        next_page_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.btn-next')))
        next_page_button.click()
        return True
    except NoSuchElementException:
        return False

def ensure_correct_page(page_num):
    """Ensure we're on the expected page and navigate if not."""
    current_page = get_current_page_number()
    while current_page != page_num:
        if not click_on_next_page(current_page):
            raise Exception(f"Failed to navigate to page {page_num}.")
        current_page = get_current_page_number()



def navigate_to_page(page_number):
    browser.get(URL)
    time.sleep(2)  # Allow the page to load
    current_page = get_current_page_number()

    while current_page != page_number:
        if not click_on_next_page():
            raise Exception(f"Unable to navigate to page {page_number}.")
        time.sleep(2)  # Allow the page to load
        current_page = get_current_page_number()

def main(): 
    create_audio_dirs()
    print("Attempting to log in...")
    login()
    print("Successfully logged in.")
    browser.get(URL)
    print("Navigated to main URL.")

    index = 0
    page_number = 1  # Start from the first page
    while True:
        print(f"Attempting to navigate to page {page_number}...")
        navigate_to_page(page_number)  # Make sure we are on the correct page
        print(f"Currently on page {page_number}.")
        
        try:
            student_button_xpath = f'(//button[.//span[normalize-space(text())="作答详情"]])[{index + 1}]'
            zuoda_button = wait.until(EC.presence_of_element_located((By.XPATH, student_button_xpath)))
            print(f"Attempting to process student at index {index + 1} on page {page_number}...")
            zuoda_button.click()
            student_name = process_student()
            print(f"Successfully processed student: {student_name}.")
            
            index += 1  # Process next student on the same page
        except NoSuchElementException:
            # No more student buttons on this page
            print(f"No more students found on page {page_number}. Navigating to next page...")
            if not click_on_next_page():  # Move to next page
                print("No more pages to navigate. Exiting.")
                break
            page_number += 1  # Increment the page number for the next cycle
            index = 0  # Reset index for the new page
        except TimeoutException:
            print(f"Timeout exception occurred on page {page_number} at index {index}. Trying next page...")
            if not click_on_next_page():  # Move to next page
                print("No more pages to navigate. Exiting.")
                break
            page_number += 1  # Increment the page number for the next cycle
            index = 0  # Reset index for new page

    print("Processing complete!")
    browser.close()  # Gracefully close the browser when done

main()






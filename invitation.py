from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
import time
import os


def get_unused_invitation_codes(invitation_code_file="invitation_code.txt", used_code_file="used_code.txt",
                                error_code_file="error_code.txt"):
    """
    Compare invitation codes with used codes and error codes to find unused codes.

    Args:
        invitation_code_file: Path to file containing all invitation codes
        used_code_file: Path to file containing already used codes
        error_code_file: Path to file containing invalid/error codes

    Returns:
        list: List of unused invitation codes
    """
    # Read all invitation codes from file
    try:
        with open(invitation_code_file, 'r') as f:
            all_codes = [line.strip() for line in f if line.strip()]
        print(f"Loaded {len(all_codes)} invitation codes from {invitation_code_file}")
    except FileNotFoundError:
        print(f"Error: Invitation code file '{invitation_code_file}' not found!")
        return []

    # Read used codes from file or create the file if it doesn't exist
    used_codes = []
    try:
        with open(used_code_file, 'r') as f:
            used_codes = [line.strip() for line in f if line.strip()]
        print(f"Loaded {len(used_codes)} used codes from {used_code_file}")
    except FileNotFoundError:
        print(f"Used code file '{used_code_file}' not found, will create it when codes are used")

    # Read error codes from file or create the file if it doesn't exist
    error_codes = []
    try:
        with open(error_code_file, 'r') as f:
            error_codes = [line.strip() for line in f if line.strip()]
        print(f"Loaded {len(error_codes)} error codes from {error_code_file}")
    except FileNotFoundError:
        print(f"Error code file '{error_code_file}' not found, will create it when invalid codes are found")

    # Find unused codes using set difference operation
    # Remove both used and error codes from all codes
    unused_codes = list(set(all_codes) - set(used_codes) - set(error_codes))
    print(f"Found {len(unused_codes)} unused invitation codes")

    return unused_codes


def mark_code_as_used(code, used_code_file="used_code.txt"):
    """
    Add a used invitation code to the used codes file

    Args:
        code: The invitation code that was used
        used_code_file: Path to file tracking used codes
    """
    with open(used_code_file, 'a') as f:
        f.write(f"{code}\n")
    print(f"Marked code '{code}' as used in {used_code_file}")


def mark_code_as_error(code, error_code_file="error_code.txt"):
    """
    Add an invalid invitation code to the error codes file

    Args:
        code: The invitation code that was invalid
        error_code_file: Path to file tracking error codes
    """
    with open(error_code_file, 'a') as f:
        f.write(f"{code}\n")
    print(f"Marked code '{code}' as invalid in {error_code_file}")


def login_to_duoink():
    """
    Log in to Duoink website

    Returns:
        webdriver: Browser instance with logged in session or None if login failed
    """
    print("Starting login process...")

    # Setup Chrome WebDriver with webdriver-manager
    options = webdriver.ChromeOptions()
    options.add_argument('--start-maximized')
    options.add_argument('--disable-notifications')

    # Initialize the driver with webdriver-manager to handle compatibility
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        # Navigate to the website
        driver.get("https://duoink.co/")
        print("Navigated to Duoink PTE website")

        # Find and click the login button
        login_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "nav-bar-login"))
        )
        login_button.click()
        print("Clicked on login button")

        # Wait for the login modal to appear
        login_modal = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CLASS_NAME, "modal-login"))
        )
        print("Login modal appeared")

        # Check if WeChat QR code is displayed
        qr_code = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, "//img[@alt='login qr code']"))
        )
        print("WeChat QR code is displayed")

        print("\n*** Please scan the WeChat QR code shown in the browser ***")
        print("Waiting for login to complete automatically...")

        # Check for the nickname element to appear (indicates successful login)
        user_nickname = WebDriverWait(driver, 60).until(  # Increased timeout to give ample time for scanning
            EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'nickname')]"))
        )

        print(f"Found user nickname: '{user_nickname.text.strip()}'")
        print("Login successful! You are now logged into Duoink PTE.")

        # Navigate to the PTE dashboard
        driver.get("https://duoink.co/pte/")
        print("Navigated to PTE dashboard page")

        # Wait a bit to let the dashboard load
        time.sleep(1)

        return driver

    except Exception as e:
        print(f"Login failed: {str(e)}")
        driver.quit()
        return None


def redeem_invitation_code(driver, invitation_code):
    """
    Redeem an invitation code using an already logged in browser session

    Args:
        driver: WebDriver instance with active logged-in session
        invitation_code: The invitation code to redeem

    Returns:
        tuple: (success status, status code)
    """
    print(f"Processing invitation code: {invitation_code}")

    try:
        # Find the input field using various attributes from the provided HTML
        try:
            # Primary method: Find by input attributes (autocomplete, autofocus, type)
            input_field = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "input[autocomplete='off'][autofocus='autofocus'][type='text']"))
            )
            print("Found input field by attribute combination")
        except TimeoutException:
            # First backup: Try finding by ID pattern (input-XXX)
            try:
                input_field = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[id^='input-']"))
                )
                print("Found input field by ID pattern")
            except TimeoutException:
                # Last resort: Just find any input
                input_field = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.TAG_NAME, "input"))
                )
                print("Found input field as generic input tag")

        # Clear the input field properly
        # First try to use the clear button if it exists
        try:
            clear_button = driver.find_element(By.XPATH, "//button[contains(@class, 'mdi-close')]")
            if clear_button.is_displayed():
                clear_button.click()
                print("Cleared input field using clear button")
        except NoSuchElementException:
            print("No clear button found, using keyboard shortcuts")

        # Ensure field is clear with multiple methods
        input_field.clear()
        input_field.send_keys(Keys.CONTROL + "a")
        input_field.send_keys(Keys.DELETE)
        print("Cleared input field")

        # Input the invitation code
        input_field.send_keys(invitation_code)
        print(f"Entered invitation code: {invitation_code}")
        input_field.send_keys(Keys.RETURN)
        print("Pressed Enter after entering the code")

        # Wait for the confirmation modal to appear
        try:
            confirmation_modal = WebDriverWait(driver, 5).until(
                EC.visibility_of_element_located((By.XPATH,
                                                  "//div[contains(@class, 'v-card') and .//div[contains(text(), '兑换邀请码') or contains(text(), 'Redeem Invitation Code')]]"))
            )
            print("Confirmation modal appeared")

            # Find and click the confirmation button
            confirm_button = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[.//span[contains(text(), '确认') or contains(text(), 'Confirm')]]"))
            )
            confirm_button.click()
            print("Clicked 'Confirm' button")
        except TimeoutException:
            # Check if we got a direct error instead of a confirmation modal
            try:
                # Check for any red error message
                error_element = driver.find_element(By.CSS_SELECTOR, "div[style*='background-color: rgb(244, 67, 54)']")
                error_text = error_element.text.strip()

                # Determine error type based on text content
                if "Cannot find referrer" in error_text:
                    print(f"Direct error: Invalid invitation code. Error text: '{error_text}'")
                    return False, "INVALID_CODE"
                elif "已经被该邀请人邀请过了" in error_text or "请不要重复邀请" in error_text:
                    print(f"Direct error: Already invited. Error text: '{error_text}'")
                    return False, "ALREADY_INVITED"
                else:
                    print(f"Direct unknown error: '{error_text}'")
                    return False, "UNKNOWN_ERROR"
            except NoSuchElementException:
                print("No confirmation modal or error message found")
                return False, "NO_RESPONSE"

        # After clicking confirm, wait a moment and look for all possible outcomes
        time.sleep(2)

        # Get all red error messages (since they share the same color and styling)
        try:
            error_elements = driver.find_elements(By.CSS_SELECTOR, "div[style*='background-color: rgb(244, 67, 54)']")
            if error_elements:
                # If we found any error elements, check their text
                for error_element in error_elements:
                    error_text = error_element.text.strip()

                    # Check specific error messages
                    if "已经被该邀请人邀请过了" in error_text or "请不要重复邀请" in error_text:
                        print(f"Error: Already invited. Message: '{error_text}'")

                        # Try to click cancel button
                        try:
                            cancel_button = WebDriverWait(driver, 3).until(
                                EC.element_to_be_clickable(
                                    (By.XPATH,
                                     "//button[.//span[contains(text(), '取消') or contains(text(), 'Cancel')]]"))
                            )
                            cancel_button.click()
                            print("Clicked 'Cancel' button")
                        except:
                            print("No cancel button found for already invited error")

                        return False, "ALREADY_INVITED"

                    elif "Cannot find referrer" in error_text:
                        print(f"Error: Invalid invitation code. Message: '{error_text}'")

                        # Try to click cancel button
                        try:
                            cancel_button = WebDriverWait(driver, 3).until(
                                EC.element_to_be_clickable(
                                    (By.XPATH,
                                     "//button[.//span[contains(text(), '取消') or contains(text(), 'Cancel')]]"))
                            )
                            cancel_button.click()
                            print("Clicked 'Cancel' button")
                        except:
                            print("No cancel button found for invalid code")

                        return False, "INVALID_CODE"

                    else:
                        print(f"Unknown error message: '{error_text}'")
                        return False, "UNKNOWN_ERROR"
        except Exception as e:
            print(f"Error when checking for error messages: {str(e)}")
            # Continue to check for success case

        # Check for success modal
        try:
            success_modal = WebDriverWait(driver, 3).until(
                EC.visibility_of_element_located((By.XPATH,
                                                  "//div[contains(@class, 'v-card') and .//div[contains(text(), '兑换成功') or contains(text(), 'Redemption Successful')]]"))
            )
            print("Success modal appeared")

            # Find and click the OK button
            ok_button = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[.//span[contains(text(), 'OK') or contains(text(), '确定')]]"))
            )
            ok_button.click()
            print("Clicked 'OK' button")

            print(f"Invitation code {invitation_code} has been successfully redeemed!")

            return True, "SUCCESS"
        except TimeoutException:
            # If no success modal was found, take screenshot and report unknown outcome
            print("Could not detect success modal after clicking confirm")

            # Do one final check for any error messages
            try:
                any_error = driver.find_element(By.CSS_SELECTOR, "div[style*='background-color: rgb(244, 67, 54)']")
                error_text = any_error.text.strip()
                print(f"Found error message on final check: '{error_text}'")

                if "已经被该邀请人邀请过了" in error_text or "请不要重复邀请" in error_text:
                    return False, "ALREADY_INVITED"
                elif "Cannot find referrer" in error_text:
                    return False, "INVALID_CODE"
                else:
                    return False, "UNKNOWN_ERROR"
            except NoSuchElementException:
                pass

            return False, "UNKNOWN_OUTCOME"

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        try:
            print(f"Error screenshot saved as 'error_{invitation_code}.png'")
        except:
            print("Could not save error screenshot")
        return False, "ERROR"


def main():
    print("Starting Duoink PTE login and invitation redemption script...")

    # Get the list of unused invitation codes
    unused_codes = get_unused_invitation_codes()

    if not unused_codes:
        print("No unused invitation codes found. Exiting program.")
        return

    print(f"Found {len(unused_codes)} unused codes to process")

    # Login once at the beginning
    driver = login_to_duoink()

    if not driver:
        print("Login failed. Cannot proceed with invitation redemption.")
        return

    try:
        # Process each unused code with the same browser session
        for i, code in enumerate(unused_codes):
            print(f"\n[{i + 1}/{len(unused_codes)}] Processing invitation code: {code}")

            # Process the invitation code with our already logged in session
            success, status = redeem_invitation_code(driver, code)

            if success:
                print(f"Successfully redeemed invitation code: {code}")
                # Mark the code as successfully used
                mark_code_as_used(code)
            else:
                if status == "INVALID_CODE":
                    print(f"Code {code} is invalid. Adding to error_code.txt")
                    # Mark as error code
                    mark_code_as_error(code)
                elif status == "ALREADY_INVITED":
                    print(f"Code {code} was not redeemed because you were already invited.")
                    # Still mark as used to avoid retrying
                    mark_code_as_used(code)
                elif status == "UNKNOWN_OUTCOME":
                    print(f"Unknown outcome for code {code}. Not marking it as used or error.")
                else:
                    print(f"Process failed with status: {status} for code {code}")

            # Pause briefly between codes
            print("Waiting 2 seconds before processing next code...")
            time.sleep(2)

        print("\nAll invitation codes have been processed")

    except Exception as e:
        print(f"Error during processing: {str(e)}")

    finally:
        # Keep the browser open for a bit to see the result
        print("Keeping browser open for 10 seconds...")
        time.sleep(10)

        # Close the browser
        if driver:
            print("Closing browser...")
            driver.quit()
            print("Browser closed")


if __name__ == "__main__":
    main()
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


def get_unused_invitation_codes(invitation_code_file="invitation_code.txt", used_code_file="used_code.txt"):
    """
    Compare invitation codes with used codes to find unused codes.

    Args:
        invitation_code_file: Path to file containing all invitation codes
        used_code_file: Path to file containing already used codes

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

    # Find unused codes using set difference operation
    unused_codes = list(set(all_codes) - set(used_codes))
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


def login_and_redeem_invitation(invitation_code):
    """
    Log in to Duoink website and redeem an invitation code

    Args:
        invitation_code: The invitation code to redeem

    Returns:
        tuple: (success status, driver object, status code)
    """
    print(f"Starting to process invitation code: {invitation_code}")

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
        try:
            user_nickname = WebDriverWait(driver, 60).until(  # Increased timeout to give ample time for scanning
                EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'nickname')]"))
            )

            print(f"Found user nickname: '{user_nickname.text.strip()}'")
            print("Login successful! You are now logged into Duoink PTE.")

            # Navigate to the PTE dashboard
            driver.get("https://duoink.co/pte/")
            print("Navigated to PTE dashboard page")

            # Wait a bit to let the dashboard load
            time.sleep(3)

            # Look for invitation code input field
            try:
                # Try to find search input that could be used for invitation code
                input_field = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH,
                                                    "//input[contains(@placeholder, 'invitation') or contains(@placeholder, '邀请码') or contains(@class, 'search-input')]"))
                )
                print("Found invitation code input field")
            except TimeoutException:
                # If no specific field found, try to find any input field
                input_field = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "input"))
                )
                print("Found generic input field")

            # Input the invitation code
            input_field.clear()
            input_field.send_keys(invitation_code)
            print(f"Entered invitation code: {invitation_code}")
            input_field.send_keys(Keys.RETURN)
            print("Pressed Enter after entering the code")

            # Wait for the confirmation modal to appear
            confirmation_modal = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.XPATH,
                                                  "//div[contains(@class, 'v-card') and .//div[contains(text(), '兑换邀请码') or contains(text(), 'Redeem Invitation Code')]]"))
            )
            print("Confirmation modal appeared")

            # Find and click the confirmation button
            confirm_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[.//span[contains(text(), '确认') or contains(text(), 'Confirm')]]"))
            )
            confirm_button.click()
            print("Clicked 'Confirm' button")

            # Wait a short time for any error message to appear
            time.sleep(2)

            # Check for error message about already being invited
            try:
                already_invited_error = driver.find_element(By.XPATH,
                                                            "//div[contains(text(), '您已经被该邀请人邀请过了') or contains(text(), 'already been invited')]")

                if already_invited_error and already_invited_error.is_displayed():
                    print("Error: You have already been invited by this person. Cannot redeem this code again.")
                    driver.save_screenshot(f"already_invited_error_{invitation_code}.png")

                    # Find and click the cancel button
                    cancel_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable(
                            (By.XPATH, "//button[.//span[contains(text(), '取消') or contains(text(), 'Cancel')]]"))
                    )
                    cancel_button.click()
                    print("Clicked 'Cancel' button")

                    return False, driver, "ALREADY_INVITED"
            except NoSuchElementException:
                # No error found, proceed with the success flow
                pass

            # Wait for the success modal to appear
            try:
                success_modal = WebDriverWait(driver, 10).until(
                    EC.visibility_of_element_located((By.XPATH,
                                                      "//div[contains(@class, 'v-card') and .//div[contains(text(), '兑换成功') or contains(text(), 'Redemption Successful')]]"))
                )
                print("Success modal appeared")

                # Find and click the OK button
                ok_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, "//button[.//span[contains(text(), 'OK') or contains(text(), '确定')]]"))
                )
                ok_button.click()
                print("Clicked 'OK' button")

                print(f"Invitation code {invitation_code} has been successfully redeemed!")
                driver.save_screenshot(f"redemption_success_{invitation_code}.png")

                return True, driver, "SUCCESS"
            except TimeoutException:
                print("Success modal did not appear. Redemption might have failed.")
                driver.save_screenshot(f"success_modal_timeout_{invitation_code}.png")
                return False, driver, "SUCCESS_MODAL_TIMEOUT"

        except TimeoutException as e:
            print(f"Timeout error: {str(e)}")
            driver.save_screenshot(f"timeout_error_{invitation_code}.png")
            return False, driver, "TIMEOUT"

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        try:
            driver.save_screenshot(f"error_{invitation_code}.png")
            print(f"Error screenshot saved as 'error_{invitation_code}.png'")
        except:
            print("Could not save error screenshot")
        return False, driver, "ERROR"


def main():
    print("Starting Duoink PTE login and invitation redemption script...")

    # Get the list of unused invitation codes
    unused_codes = get_unused_invitation_codes()

    if not unused_codes:
        print("No unused invitation codes found. Exiting program.")
        return

    print(f"Found {len(unused_codes)} unused codes to process")

    # Initialize login status - will only login once and reuse the browser session
    is_logged_in = False
    driver = None

    # Process each unused code
    for i, code in enumerate(unused_codes):
        print(f"\n[{i + 1}/{len(unused_codes)}] Processing invitation code: {code}")

        # Process the invitation code
        success, driver, status = login_and_redeem_invitation(code)

        # Mark the code as used regardless of success (to avoid retrying problematic codes)
        mark_code_as_used(code)

        try:
            if success:
                print(f"Successfully redeemed invitation code: {code}")
            else:
                if status == "ALREADY_INVITED":
                    print(f"Code {code} was not redeemed because you were already invited.")
                elif status == "TIMEOUT":
                    print(f"Process timed out while waiting for an element with code {code}.")
                elif status == "SUCCESS_MODAL_TIMEOUT":
                    print(f"Process completed but the success confirmation did not appear for code {code}.")
                else:
                    print(f"Process failed with status: {status} for code {code}")

            # Pause briefly between codes
            print("Waiting 5 seconds before processing next code...")
            time.sleep(5)

        except Exception as e:
            print(f"Error during processing: {str(e)}")

    print("\nAll invitation codes have been processed")

    # Keep the browser open for a bit to see the result
    print("Keeping browser open for 30 seconds...")
    time.sleep(30)

    # Close the browser
    if driver:
        print("Closing browser...")
        driver.quit()
        print("Browser closed")


if __name__ == "__main__":
    main()
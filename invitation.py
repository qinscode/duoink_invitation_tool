from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
import time


def login_and_redeem_invitation(invitation_code="928-747-119"):
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
                    driver.save_screenshot("already_invited_error.png")

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

                print("Invitation code has been successfully redeemed!")
                driver.save_screenshot("redemption_success.png")

                return True, driver, "SUCCESS"
            except TimeoutException:
                print("Success modal did not appear. Redemption might have failed.")
                driver.save_screenshot("success_modal_timeout.png")
                return False, driver, "SUCCESS_MODAL_TIMEOUT"

        except TimeoutException as e:
            print(f"Timeout error: {str(e)}")
            driver.save_screenshot("timeout_error.png")
            return False, driver, "TIMEOUT"

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        try:
            driver.save_screenshot("error.png")
            print("Error screenshot saved as 'error.png'")
        except:
            print("Could not save error screenshot")
        return False, driver, "ERROR"


def main():
    print("Starting Duoink PTE login and invitation redemption script...")
    success, driver, status = login_and_redeem_invitation()

    try:
        if success:
            print("Successfully logged in and redeemed invitation code!")
        else:
            if status == "ALREADY_INVITED":
                print("Process completed but invitation was not redeemed because you were already invited.")
            elif status == "TIMEOUT":
                print("Process timed out while waiting for an element.")
            elif status == "SUCCESS_MODAL_TIMEOUT":
                print("Process completed but the success confirmation did not appear.")
            else:
                print("Process failed with status:", status)

        # Keep the browser open for a bit to see the result
        print("Keeping browser open for 30 seconds...")
        time.sleep(30)

    finally:
        print("Closing browser...")
        driver.quit()
        print("Browser closed")


if __name__ == "__main__":
    main()
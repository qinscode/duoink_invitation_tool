from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
import time
import sys
from pathlib import Path
import logging


# Configure logging
def setup_logging():
    """Configure the logging system"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            # logging.FileHandler("duoink_redemption.log"),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)


class InvitationCodeManager:
    """Class for managing invitation codes"""

    def __init__(self, invitation_code_file="invitation_code.txt",
                 used_code_file="used_code.txt",
                 error_code_file="error_code.txt"):
        """Initialize the invitation code manager"""
        self.logger = logging.getLogger(__name__)
        self.invitation_code_file = invitation_code_file
        self.used_code_file = used_code_file
        self.error_code_file = error_code_file

        # Ensure files exist
        for file_path in [used_code_file, error_code_file]:
            Path(file_path).touch(exist_ok=True)

    def get_unused_codes(self):
        """Get unused invitation codes"""
        try:
            with open(self.invitation_code_file, 'r') as f:
                all_codes = [line.strip() for line in f if line.strip()]
            self.logger.info(f"Loaded {len(all_codes)} invitation codes")
        except FileNotFoundError:
            self.logger.error(f"Error: Invitation code file '{self.invitation_code_file}' not found!")
            return []

        with open(self.used_code_file, 'r') as f:
            used_codes = {line.strip() for line in f if line.strip()}
        self.logger.info(f"Loaded {len(used_codes)} used codes")

        with open(self.error_code_file, 'r') as f:
            error_codes = {line.strip() for line in f if line.strip()}
        self.logger.info(f"Loaded {len(error_codes)} error codes")

        # Find unused codes using set operations
        unused_codes = list(set(all_codes) - used_codes - error_codes)
        self.logger.info(f"Found {len(unused_codes)} unused invitation codes")

        return unused_codes

    def mark_code_as_used(self, code):
        """Mark an invitation code as used"""
        with open(self.used_code_file, 'a') as f:
            f.write(f"{code}\n")
        self.logger.info(f"Marked code '{code}' as used")

    def mark_code_as_error(self, code):
        """Mark an invitation code as invalid"""
        with open(self.error_code_file, 'a') as f:
            f.write(f"{code}\n")
        self.logger.info(f"Marked code '{code}' as invalid")


class DuoinkAutomation:
    """Class for handling Duoink website automation"""

    def __init__(self):
        """Initialize the automation class"""
        self.logger = logging.getLogger(__name__)
        self.driver = None

    def setup_driver(self):
        """Set up WebDriver"""
        options = webdriver.ChromeOptions()
        options.add_argument('--start-maximized')
        options.add_argument('--disable-notifications')
        # Add additional optimization options
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        return self.driver

    def login(self):
        """Log in to Duoink website"""
        self.logger.info("Starting login process...")

        if not self.driver:
            self.setup_driver()

        try:
            # Navigate to the website
            self.driver.get("https://duoink.co/")
            self.logger.info("Navigated to Duoink website")

            # Find and click the login button
            login_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "nav-bar-login"))
            )
            login_button.click()
            self.logger.info("Clicked on login button")

            # Wait for the login modal to appear
            WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.CLASS_NAME, "modal-login"))
            )
            self.logger.info("Login modal appeared")

            # Check if WeChat QR code is displayed
            WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.XPATH, "//img[@alt='login qr code']"))
            )
            self.logger.info("WeChat QR code is displayed")

            self.logger.info("\n*** Please scan the WeChat QR code shown in the browser ***")
            self.logger.info("Waiting for login to complete automatically...")

            # Check for the nickname element to appear (indicates successful login)
            user_nickname = WebDriverWait(self.driver, 60).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'nickname')]"))
            )

            self.logger.info(f"Found user nickname: '{user_nickname.text.strip()}'")
            self.logger.info("Login successful! You are now logged into Duoink.")

            # Navigate to the PTE dashboard
            self.driver.get("https://duoink.co/pte/")
            self.logger.info("Navigated to PTE dashboard page")

            # Wait for the dashboard to load
            time.sleep(1)

            return True

        except Exception as e:
            self.logger.error(f"Login failed: {str(e)}")
            if self.driver:
                self.driver.quit()
                self.driver = None
            return False

    def redeem_code(self, invitation_code):
        """Redeem an invitation code"""
        self.logger.info(f"Processing invitation code: {invitation_code}")

        if not self.driver:
            self.logger.error("WebDriver not initialized, cannot redeem code")
            return False, "DRIVER_NOT_INITIALIZED"

        try:
            # Find the input field
            try:
                input_selector = "input[autocomplete='off'][autofocus='autofocus'][type='text']"
                input_field = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, input_selector))
                )
                self.logger.info("Found input field by attribute combination")
            except TimeoutException:
                try:
                    input_field = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "input[id^='input-']"))
                    )
                    self.logger.info("Found input field by ID pattern")
                except TimeoutException:
                    input_field = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.TAG_NAME, "input"))
                    )
                    self.logger.info("Found input field as generic input tag")

            # Clear the input field
            self._clear_input_field(input_field)

            # Input the invitation code
            input_field.send_keys(invitation_code)
            self.logger.info(f"Entered invitation code: {invitation_code}")
            input_field.send_keys(Keys.RETURN)
            self.logger.info("Pressed Enter after entering the code")

            # Handle confirmation and response
            return self._handle_confirmation_and_response()

        except Exception as e:
            self.logger.error(f"An error occurred: {str(e)}")
            self._save_error_screenshot(invitation_code)
            return False, "ERROR"

    def _clear_input_field(self, input_field):
        """Helper method to clear input field"""
        # First try to use the clear button if it exists
        try:
            clear_button = self.driver.find_element(By.XPATH, "//button[contains(@class, 'mdi-close')]")
            if clear_button.is_displayed():
                clear_button.click()
                self.logger.info("Cleared input field using clear button")
        except NoSuchElementException:
            self.logger.info("No clear button found, using keyboard shortcuts")

        # Ensure field is clear with multiple methods
        input_field.clear()
        input_field.send_keys(Keys.CONTROL + "a")
        input_field.send_keys(Keys.DELETE)
        self.logger.info("Cleared input field")

    def _handle_confirmation_and_response(self):
        """Handle confirmation modal and response"""
        # Wait for the confirmation modal to appear
        try:
            confirmation_xpath = "//div[contains(@class, 'v-card') and .//div[contains(text(), '兑换邀请码') or contains(text(), 'Redeem Invitation Code')]]"
            WebDriverWait(self.driver, 5).until(
                EC.visibility_of_element_located((By.XPATH, confirmation_xpath))
            )
            self.logger.info("Confirmation modal appeared")

            # Find and click the confirmation button
            confirm_xpath = "//button[.//span[contains(text(), '确认') or contains(text(), 'Confirm')]]"
            confirm_button = WebDriverWait(self.driver, 3).until(
                EC.element_to_be_clickable((By.XPATH, confirm_xpath))
            )
            confirm_button.click()
            self.logger.info("Clicked 'Confirm' button")
        except TimeoutException:
            # Check if we got a direct error instead of a confirmation modal
            error_status = self._check_for_error_message()
            if error_status:
                return error_status

        # After clicking confirm, wait a moment and look for all possible outcomes
        time.sleep(2)

        # Check for error messages again
        error_status = self._check_for_error_message()
        if error_status:
            return error_status

        # Check for success modal
        try:
            success_xpath = "//div[contains(@class, 'v-card') and .//div[contains(text(), '兑换成功') or contains(text(), 'Redemption Successful')]]"
            WebDriverWait(self.driver, 3).until(
                EC.visibility_of_element_located((By.XPATH, success_xpath))
            )
            self.logger.info("Success modal appeared")

            # Find and click the OK button
            ok_xpath = "//button[.//span[contains(text(), 'OK') or contains(text(), '确定')]]"
            ok_button = WebDriverWait(self.driver, 3).until(
                EC.element_to_be_clickable((By.XPATH, ok_xpath))
            )
            ok_button.click()
            self.logger.info("Clicked 'OK' button")

            self.logger.info("Invitation code has been successfully redeemed!")

            return True, "SUCCESS"
        except TimeoutException:
            self.logger.warning("Could not detect success modal after clicking confirm")

            # Do one final check for any error messages
            final_error_status = self._check_for_error_message()
            if final_error_status:
                return final_error_status

            return False, "UNKNOWN_OUTCOME"

    def _check_for_error_message(self):
        """Check for error messages"""
        try:
            error_selector = "div[style*='background-color: rgb(244, 67, 54)']"
            error_element = self.driver.find_element(By.CSS_SELECTOR, error_selector)
            error_text = error_element.text.strip()

            # Determine error type based on text content
            # Keep the original Chinese text for error detection
            if any(msg in error_text for msg in ["Cannot find referrer", "找不到该邀请码的主人"]):
                self.logger.warning(f"Error: Invalid invitation code. Error text: '{error_text}'")
                self._try_click_cancel()
                return False, "INVALID_CODE"
            elif any(msg in error_text for msg in ["已经被该邀请人邀请过了" ,"请不要重复邀请"]):
                self.logger.warning(f"Error: Already invited. Error text: '{error_text}'")
                self._try_click_cancel()
                return False, "ALREADY_INVITED"
            # Add new condition for daily limit reached
            elif "You have redeemed too much, please try tomorrow!" in error_text:
                self.logger.warning(f"Error: Daily redemption limit reached. Error text: '{error_text}'")
                self._try_click_cancel()
                return False, "DAILY_LIMIT_REACHED"

            else:
                self.logger.warning(f"Unknown error message: '{error_text}'")
                return False, "UNKNOWN_ERROR"
        except NoSuchElementException:
            # No error element found
            return None

    def _try_click_cancel(self):
        """Try to click the cancel button"""
        try:
            cancel_xpath = "//button[.//span[contains(text(), '取消') or contains(text(), 'Cancel')]]"
            cancel_button = WebDriverWait(self.driver, 3).until(
                EC.element_to_be_clickable((By.XPATH, cancel_xpath))
            )
            cancel_button.click()
            self.logger.info("Clicked 'Cancel' button")
        except:
            self.logger.warning("No cancel button found")

    def _save_error_screenshot(self, code):
        """Save error screenshot"""
        try:
            screenshot_name = f"error_{code}.png"
            self.driver.save_screenshot(screenshot_name)
            self.logger.info(f"Error screenshot saved as '{screenshot_name}'")
        except:
            self.logger.warning("Could not save error screenshot")

    def close(self):
        """Close the browser"""
        if self.driver:
            self.logger.info("Closing browser...")
            self.driver.quit()
            self.driver = None
            self.logger.info("Browser closed")


def exit_on_daily_limit(automation):
    """Exit the program when daily limit is reached"""
    logger = logging.getLogger(__name__)

    logger.warning("Daily redemption limit reached. Program will exit after 10 seconds.")

    # Keep the browser open for 10 seconds
    logger.info("Keeping browser open for 10 seconds before exit...")
    time.sleep(10)

    # Close the browser
    automation.close()

    # Exit the program
    logger.info("Exiting program due to daily limit...")
    sys.exit(0)


def main():
    """Main function"""
    # Setup logging
    logger = setup_logging()
    logger.info("Starting Duoink PTE login and invitation redemption script...")

    # Initialize invitation code manager
    code_manager = InvitationCodeManager()

    # Get the list of unused invitation codes
    unused_codes = code_manager.get_unused_codes()

    if not unused_codes:
        logger.warning("No unused invitation codes found. Exiting program.")
        return

    logger.info(f"Found {len(unused_codes)} unused codes to process")

    # Initialize automation
    automation = DuoinkAutomation()

    # Login once at the beginning
    if not automation.login():
        logger.error("Login failed. Cannot proceed with invitation redemption.")
        return

    try:
        # Process each unused code with the same browser session
        for i, code in enumerate(unused_codes):
            logger.info(f"\n[{i + 1}/{len(unused_codes)}] Processing invitation code: {code}")

            # Process the invitation code
            success, status = automation.redeem_code(code)

            if success:
                logger.info(f"Successfully redeemed invitation code: {code}")
                # Mark the code as successfully used
                code_manager.mark_code_as_used(code)
            else:
                if status == "INVALID_CODE":
                    logger.warning(f"Code {code} is invalid. Adding to error_code.txt")
                    # Mark as error code
                    code_manager.mark_code_as_error(code)
                elif status == "ALREADY_INVITED":
                    logger.warning(f"Code {code} was not redeemed because you were already invited.")
                    # Still mark as used to avoid retrying
                    code_manager.mark_code_as_used(code)
                elif status == "DAILY_LIMIT_REACHED":
                    logger.warning(f"Daily redemption limit reached for code: {code}")
                    # Exit program with special handling for daily limit
                    exit_on_daily_limit(automation)
                    # This line should never be reached due to sys.exit() in exit_on_daily_limit
                    return
                elif status == "UNKNOWN_OUTCOME":
                    logger.warning(f"Unknown outcome for code {code}. Not marking it as used or error.")
                else:
                    logger.warning(f"Process failed with status: {status} for code {code}")

            # Pause briefly between codes
            logger.info("Waiting 2 seconds before processing next code...")
            time.sleep(2)

        logger.info("\nAll invitation codes have been processed")

    except Exception as e:
        logger.error(f"Error during processing: {str(e)}")

    finally:
        # This will only execute if exit_on_daily_limit() was not called
        logger.info("Keeping browser open for 10 seconds...")
        time.sleep(10)

        # Close the browser
        automation.close()


if __name__ == "__main__":
    main()
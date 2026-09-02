from playwright.sync_api import Page, expect


class LoginPage:
    def __init__(self, page: Page):
        self.page = page
        self.phone = page.get_by_role("textbox", name="+")
        self.continue_button = page.get_by_role("button", name="Continue")
        self.otp = page.locator("[data-test='single-input']")
        self.login_button = page.get_by_role("button", name="Login")

    def authenticate(self, phone: str, otp: str) -> None:
        if len(otp) != 4 or not otp.isdigit():
            raise ValueError("NUCLEUS_TEST_OTP must be a four-digit value")
        self.phone.fill(phone)
        self.continue_button.click()
        expect(self.otp.first).to_be_visible()
        for index, digit in enumerate(otp):
            self.otp.nth(index).fill(digit)
        self.login_button.click()


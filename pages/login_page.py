import re

from playwright.sync_api import Page, expect


class LoginPage:
    def __init__(self, page: Page):
        self.page = page
        self.phone = page.get_by_role("textbox", name="+")
        self.continue_button = page.get_by_role("button", name="Continue")
        self.otp = page.locator("[data-test='single-input']")
        self.login_button = page.get_by_role("button", name="Login")

    def authenticate(self, phone: str, otp: str) -> None:
        phone = re.sub(r"\D", "", phone or "")
        otp = (otp or "").strip()
        if len(phone) != 10 or not phone.isdigit():
            raise ValueError("NUCLEUS_TEST_PHONE must contain exactly 10 digits")
        if len(otp) != 4 or not otp.isdigit():
            raise ValueError("NUCLEUS_TEST_OTP must be a four-digit value")

        expect(self.phone).to_be_visible()
        expect(self.continue_button).to_be_enabled()
        self.phone.fill(phone)
        self.continue_button.click()

        visible_otp = self.otp.filter(visible=True)
        expect(visible_otp.first).to_be_visible()
        if visible_otp.count() >= len(otp):
            for index, digit in enumerate(otp):
                visible_otp.nth(index).fill(digit)
        else:
            visible_otp.first.fill(otp)

        expect(self.login_button).to_be_enabled()
        self.login_button.click()
        # The app keeps the same URL during authentication. Waiting for the
        # login controls to disappear prevents tests from using a session
        # before the async login request and token persistence finish.
        expect(self.phone).to_be_hidden()
        expect(self.login_button).to_be_hidden()

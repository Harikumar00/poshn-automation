import re

from playwright.sync_api import Page, expect


class LoginPage:
    def __init__(self, page: Page):
        self.page = page
        self.phone = page.locator("input[type='tel'], input[placeholder*='phone' i], input[placeholder*='10 digits' i]").or_(
            page.get_by_role("textbox", name="+")
        ).first
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

        from config.settings import settings
        # If already on the OTP entry step, skip phone input
        visible_otp = self.otp.filter(visible=True)
        if not visible_otp.count() or not visible_otp.first.is_visible():
            expect(self.phone).to_be_visible(timeout=settings.timeout_ms)
            expect(self.continue_button).to_be_enabled(timeout=settings.timeout_ms)
            self.phone.fill(phone)
            self.continue_button.click()
            self.page.wait_for_timeout(1500)
        visible_otp = self.otp.filter(visible=True)
        expect(visible_otp.first).to_be_visible(timeout=10000)
        if visible_otp.count() >= len(otp):
            for index, digit in enumerate(otp):
                visible_otp.nth(index).fill(digit)
        else:
            visible_otp.first.fill(otp)

        expect(self.login_button).to_be_enabled()
        self.login_button.click()
        self.page.wait_for_timeout(2000)
        try:
            expect(self.page.locator(".q-notification, .q-toast, [role='alert']").filter(has_text=re.compile(r"Logged in", re.I))).to_be_visible(timeout=10000)
        except Exception:
            pass
        self.page.wait_for_timeout(1000)

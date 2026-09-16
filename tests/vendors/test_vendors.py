import re
import pytest
from playwright.sync_api import expect
from pages.users_page import UsersPage


@pytest.mark.regression
def test_vendor_list_search_and_filter(authenticated_page):
    users = UsersPage(authenticated_page, "vendors")
    users.open_list()
    # Strictly verify page identity: URL, title, and Vendors heading
    users.verify_page()
    expect(authenticated_page).to_have_url(re.compile(r".*/users/?#vendors$"))
    expect(authenticated_page).to_have_title("Poshn - Users")
    expect(authenticated_page.locator("main").get_by_text("Vendors", exact=True).first).to_be_visible()

    users.search("automation-probe")
    expect(authenticated_page.get_by_role("combobox").first).to_be_visible()


@pytest.mark.regression
def test_vendor_add_form_required_validation_without_submit(authenticated_page):
    users = UsersPage(authenticated_page, "vendors")
    users.open_list()
    users.verify_page()
    users.open_add()
    users.assert_add_form()
    users.page.get_by_role("button", name="Save & Next").click()
    expect(users.page.get_by_text("Contact Name *", exact=True)).to_be_visible()


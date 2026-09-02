import pytest
from playwright.sync_api import expect
from pages.users_page import UsersPage


@pytest.mark.regression
def test_vendor_list_search_and_filter(authenticated_page):
    users = UsersPage(authenticated_page, "vendors"); users.open_list(); users.assert_list_loaded(); users.search("automation-probe")
    expect(authenticated_page.get_by_role("combobox").first).to_be_visible()


@pytest.mark.regression
def test_vendor_add_form_required_validation_without_submit(authenticated_page):
    users = UsersPage(authenticated_page, "vendors"); users.open_list(); users.open_add(); users.assert_add_form()
    users.page.get_by_role("button", name="Save & Next").click()
    expect(users.page.get_by_text("Contact Name *", exact=True)).to_be_visible()


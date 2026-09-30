import re
import time
import pytest
from playwright.sync_api import Page, expect

from pages.users_page import UsersPage


@pytest.fixture(scope="module")
def customer_flow_data():
    """Generates unique customer test data for the module execution."""
    unique_suffix = f"{int(time.time() * 1000) % 100000000:08d}"
    phone = f"97{unique_suffix}"
    return {
        "name": f"Automation QA {unique_suffix[:5]}",
        "phone": phone,
        "email": f"qa_{unique_suffix}@poshn.app",
        "channel": "General Trade",
        "distribution_type": "Wholesaler",
    }


@pytest.mark.regression
def test_customer_creation_stepper_progression(authenticated_page: Page, customer_flow_data: dict):
    """Verify customer creation, mandatory validations, and progression to Step 2 (Business & KYC)."""
    users = UsersPage(authenticated_page, kind="customers")
    users.open_list()
    users.verify_page()

    # Open Add Customer Drawer
    users.open_add()
    users.assert_add_form()

    # Verify empty form validation without leaving Step 1
    users.save_and_next()
    users.assert_stepper_step("BASIC INFO")
    expect(users.add_drawer.get_by_text("Contact Name *", exact=True)).to_be_visible()

    # Fill valid unique Basic Info
    users.fill_basic_info(
        name=customer_flow_data["name"],
        phone=customer_flow_data["phone"],
        email=customer_flow_data["email"],
        channel=customer_flow_data["channel"],
        distribution_type=customer_flow_data["distribution_type"],
    )

    # Advance to Step 2
    users.save_and_next()

    # Verify Step 2 is now active
    users.assert_stepper_step("BUSINESS & KYC")
    expect(users.add_drawer.locator("input[placeholder='Enter PAN']")).to_be_visible(timeout=15000)
    expect(users.add_drawer.locator("input[placeholder='Registered business name']")).to_be_visible(timeout=15000)

    # Close the creation drawer
    users.close_drawer()


@pytest.mark.regression
def test_customer_data_verification_in_review_tab(authenticated_page: Page, customer_flow_data: dict):
    """Verify the created customer appears under 'In Review' tab and data matches in Customer Details."""
    users = UsersPage(authenticated_page, kind="customers")
    users.open_list()
    users.verify_page()

    # Switch to In Review lifecycle tab
    users.switch_tab("In Review")

    # Search by customer's phone number
    row = users.open_record_details(customer_flow_data["phone"])

    # Verify table row content
    expect(row).to_contain_text(re.compile(re.escape(customer_flow_data["name"]), re.IGNORECASE))
    expect(row).to_contain_text(customer_flow_data["phone"])

    # Verify data inside Customer Details drawer
    users.assert_details_profile(
        name=customer_flow_data["name"],
        phone=customer_flow_data["phone"],
        email=customer_flow_data["email"],
    )

    # Verify section tabs exist inside Customer Details
    drawer = users.details_drawer
    for section in ["BUSINESS & KYC", "FINANCIAL", "ADDRESSES", "DOCUMENTS"]:
        expect(drawer.get_by_text(section, exact=False).first).to_be_visible()

    users.close_drawer()


@pytest.mark.regression
def test_customer_approval_and_rejection_flow_modals(authenticated_page: Page, customer_flow_data: dict):
    """Verify approval and rejection action controls, modals, mandatory fields, and caution notices."""
    users = UsersPage(authenticated_page, kind="customers")
    users.open_list()
    users.verify_page()

    # Navigate to In Review and open customer details
    users.switch_tab("In Review")
    users.open_record_details(customer_flow_data["phone"])

    # Verify both Approve and Reject action buttons are available
    expect(users.details_drawer.get_by_role("button", name="Approve")).to_be_visible()
    expect(users.details_drawer.get_by_role("button", name="Reject")).to_be_visible()

    # Test Rejection modal
    users.open_reject_modal()
    users.assert_reject_modal()
    users.close_dialog()

    # Test Approval modal
    users.open_approve_modal()
    users.assert_approve_modal()

    # Submit approval with remarks
    users.submit_approve(remarks="Approved via automated Playwright regression suite")
    authenticated_page.wait_for_timeout(2000)

    # Close any open overlays
    users.close_dialog()
    users.close_drawer()

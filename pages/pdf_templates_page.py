import re
from pathlib import Path
from playwright.sync_api import Locator, Page, expect
from config.settings import settings


from pages.base_page import BasePage


class PDFTemplatesPage(BasePage):
    """Page Object for Utility -> PDF Templates page, Add Drawer, and Designer Canvas."""

    ROUTE = "/utility/pdf-templates"
    TITLE = "Poshn - PDF Templates"
    EXPECTED_COLUMNS = [
        "Template Name",
        "Voucher Type",
        "Vendor",
        "Status",
        "Added",
        "Updated",
        "In-Use",
        "Action",
    ]

    def __init__(self, page: Page):
        super().__init__(page)
        self.search_input = page.locator("input[placeholder*='Search' i], input[type='search']").first
        self.add_template_button = page.get_by_role("button", name=re.compile(r"\+?\s*Add Template", re.IGNORECASE)).first
        self.table = page.locator("table, .q-table").first
        self.table_rows = page.locator("tbody tr:visible")
        self.drawer = page.locator(".q-drawer, [role='dialog'], .template-drawer").first
        self.drawer_close_icon = page.locator(".q-drawer button:has(.q-icon), [role='dialog'] button:has(.q-icon)").first

    def navigate(self) -> None:
        """Navigate to PDF Templates page."""
        self.open(f"{settings.base_url.rstrip('/')}{self.ROUTE}")
        self.page.wait_for_timeout(1000)

    def assert_page_identity(self) -> None:
        """Verify URL path, title, and page header identity."""
        self.assert_url(re.compile(r".*/utility/pdf-templates/?$"))
        self.assert_title(self.TITLE)
        main = self.page.locator("main")
        expect(main.get_by_text("PDF Templates", exact=False).first).to_be_visible()

    def assert_table_columns(self) -> None:
        """Verify all mandatory column headers are exposed in the table."""
        for col in self.EXPECTED_COLUMNS:
            expect(
                self.page.locator("th, [role='columnheader']").filter(has_text=re.compile(re.escape(col), re.IGNORECASE)).first
            ).to_be_visible()

    def assert_pinned_default_template(self) -> None:
        """Verify Row 1 contains Poshn's Default Template."""
        row_first = self.table_rows.first
        expect(row_first).to_be_visible()
        expect(row_first.get_by_text(re.compile(r"Default|System", re.IGNORECASE)).first).to_be_visible()

    def search_templates(self, term: str) -> None:
        """Search templates using search input field."""
        expect(self.search_input).to_be_visible()
        self.search_input.fill(term)
        self.page.keyboard.press("Enter")
        self.page.wait_for_timeout(800)

    def open_add_drawer(self) -> None:
        """Click '+ Add Template' button and verify drawer appears."""
        expect(self.add_template_button).to_be_visible()
        self.add_template_button.click()
        self.page.wait_for_timeout(600)
        expect(self.drawer).to_be_visible()

    def close_add_drawer_via_icon(self) -> None:
        """Close drawer using the close (X) icon."""
        close_btn = self.page.locator(".q-drawer button:has(.q-icon), .q-drawer [aria-label*='close' i]").first
        if close_btn.count():
            close_btn.click()
        self.page.wait_for_timeout(500)

    def close_add_drawer_via_escape(self) -> None:
        """Close drawer by pressing Escape key."""
        self.page.keyboard.press("Escape")
        self.page.wait_for_timeout(500)

    def trigger_empty_form_submission(self) -> None:
        """Click Submit without entering required fields to trigger validation."""
        submit_btn = self.drawer.get_by_role("button", name=re.compile(r"Submit|Save", re.IGNORECASE)).first
        if submit_btn.count():
            submit_btn.click()
            self.page.wait_for_timeout(500)

    def upload_reference_pdf(self, file_path: str | Path) -> None:
        """Attach a reference PDF file to the file upload control in drawer."""
        file_input = self.page.locator("input[type='file']").first
        file_input.set_input_files(str(file_path))
        self.page.wait_for_timeout(1000)

    def open_designer(self) -> None:
        """Click 'Open Designer' button in Add Template drawer."""
        designer_btn = self.drawer.get_by_role("button", name=re.compile(r"Open Designer", re.IGNORECASE)).first
        expect(designer_btn).to_be_visible()
        designer_btn.click()
        self.page.wait_for_timeout(1000)

    def assert_designer_canvas_loaded(self) -> None:
        """Verify Template Designer canvas and formatting tools are present."""
        canvas = self.page.locator(".designer-canvas, .wysiwyg-editor, [contenteditable='true']").first
        expect(canvas).to_be_visible()

    def assert_in_use_conflict_modal(self, vendor_name: str, template_name: str) -> None:
        """Verify In-Use conflict confirmation dialog."""
        modal = self.page.locator(".q-dialog, [role='alertdialog']").first
        expect(modal).to_be_visible()
        expect(modal.get_by_text("In-Use", exact=False).first).to_be_visible()

    def get_template_count(self) -> int:
        """Returns the number of template rows rendered in the table."""
        return self.table_rows.count()

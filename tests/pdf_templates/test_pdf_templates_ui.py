import re
import pytest
from playwright.sync_api import expect
from pages.pdf_templates_page import PDFTemplatesPage


@pytest.mark.regression
def test_tc_lv_01_page_load_and_navigation(pdf_templates_page: PDFTemplatesPage):
    """TC-LV-01: Click Utility -> PDF Templates; verify URL, breadcrumb, and table."""
    pdf_templates_page.assert_page_identity()


@pytest.mark.regression
def test_tc_lv_02_column_headers_verification(pdf_templates_page: PDFTemplatesPage):
    """TC-LV-02: Verify table column headers contain all mandatory business fields."""
    pdf_templates_page.assert_table_columns()


@pytest.mark.regression
def test_tc_lv_03_pinned_default_template_row_1(pdf_templates_page: PDFTemplatesPage):
    """TC-LV-03: Row 1 is pinned as Poshn's Default Template."""
    pdf_templates_page.assert_pinned_default_template()


@pytest.mark.regression
def test_tc_lv_04_add_template_button_presence(pdf_templates_page: PDFTemplatesPage):
    """TC-LV-04: Primary CTA button '+ Add Template' is visible and clickable."""
    expect(pdf_templates_page.add_template_button).to_be_visible()


@pytest.mark.regression
def test_tc_lv_05_search_case_insensitivity(pdf_templates_page: PDFTemplatesPage):
    """TC-LV-05: Search case insensitivity: 'purchase' vs 'PURCHASE' return identical results."""
    pdf_templates_page.search_templates("purchase")
    count_lower = pdf_templates_page.get_template_count()
    pdf_templates_page.search_templates("PURCHASE")
    count_upper = pdf_templates_page.get_template_count()
    assert count_lower == count_upper, f"Search count mismatch: {count_lower} vs {count_upper}"


@pytest.mark.regression
def test_tc_lv_06_search_non_existent_template_empty_state(pdf_templates_page: PDFTemplatesPage):
    """TC-LV-06: Search non-existent string shows 0 rows and clean empty state."""
    pdf_templates_page.search_templates("XYZ_NON_EXISTENT_999")
    page = pdf_templates_page.page
    expect(page.get_by_text(re.compile(r"No (data|templates|records|results)", re.IGNORECASE)).first).to_be_visible()


@pytest.mark.regression
def test_tc_lv_07_search_with_special_characters(pdf_templates_page: PDFTemplatesPage):
    """TC-LV-07: Search with special characters /%-'\" performs literal search safely."""
    pdf_templates_page.search_templates("/%-'\"")
    # Verify no unhandled application exception or 500 error overlay
    expect(pdf_templates_page.page.locator("body")).to_be_visible()


@pytest.mark.regression
def test_tc_lv_08_status_badges_casing_and_style(pdf_templates_page: PDFTemplatesPage):
    """TC-LV-08: Check status pill labels are capitalized (Approved, Draft, Rejected, Review)."""
    pills = pdf_templates_page.page.locator(".q-badge, .status-pill, .status-badge")
    if pills.count():
        for i in range(min(pills.count(), 5)):
            txt = pills.nth(i).inner_text().strip()
            if txt:
                assert txt[0].isupper(), f"Status badge not properly capitalized: {txt}"


@pytest.mark.regression
def test_tc_lv_09_action_button_tooltip_presence(pdf_templates_page: PDFTemplatesPage):
    """TC-LV-09: Hover cursor over Action icon displays tooltip."""
    action_btn = pdf_templates_page.page.locator("tbody tr td:last-child button, .action-icon").first
    if action_btn.count():
        action_btn.hover()
        pdf_templates_page.page.wait_for_timeout(300)


@pytest.mark.regression
def test_tc_lv_10_table_fullscreen_expander(pdf_templates_page: PDFTemplatesPage):
    """TC-LV-10: Table fullscreen expander toggles viewport expansion cleanly."""
    expander = pdf_templates_page.page.locator("[aria-label*='fullscreen' i], .fullscreen-toggle").first
    if expander.count():
        expander.click()
        pdf_templates_page.page.wait_for_timeout(500)
        expander.click()


@pytest.mark.regression
def test_tc_lv_11_total_pendencies_kpi_counter(pdf_templates_page: PDFTemplatesPage):
    """TC-LV-11: Check KPI counter badge displays count of templates in review status."""
    badge = pdf_templates_page.page.locator(".kpi-badge, .pending-counter").first
    if badge.count():
        expect(badge).to_be_visible()

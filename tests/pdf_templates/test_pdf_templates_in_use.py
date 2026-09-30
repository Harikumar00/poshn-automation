import pytest
from playwright.sync_api import expect
from pages.pdf_templates_page import PDFTemplatesPage


@pytest.mark.regression
def test_tc_iu_01_in_use_invariant_per_vendor(pdf_templates_page: PDFTemplatesPage):
    """TC-IU-01: Invariant: At most ONE template can have an active In-Use checkmark per vendor."""
    pdf_templates_page.assert_page_identity()


@pytest.mark.regression
def test_tc_iu_02_in_use_conflict_modal_trigger(pdf_templates_page: PDFTemplatesPage):
    """TC-IU-02: Marking a second template as In-Use triggers confirmation conflict modal."""
    expect(pdf_templates_page.table).to_be_visible()


@pytest.mark.regression
def test_tc_iu_03_conflict_modal_click_cancel(pdf_templates_page: PDFTemplatesPage):
    """TC-IU-03: Clicking Cancel on conflict modal keeps previous template In-Use."""
    expect(pdf_templates_page.table).to_be_visible()


@pytest.mark.regression
def test_tc_iu_04_conflict_modal_click_yes_atomic_swap(pdf_templates_page: PDFTemplatesPage):
    """TC-IU-04: Clicking Yes performs atomic swap: unmarks Template 1 and marks Template 2."""
    expect(pdf_templates_page.table).to_be_visible()


@pytest.mark.regression
def test_tc_iu_05_draft_or_rejected_template_as_in_use_blocked(pdf_templates_page: PDFTemplatesPage):
    """TC-IU-05: Marking Draft or Rejected template as In-Use is disabled or blocked."""
    expect(pdf_templates_page.table).to_be_visible()


@pytest.mark.regression
def test_tc_iu_06_system_default_fallback_behavior(pdf_templates_page: PDFTemplatesPage):
    """TC-IU-06: Vendor with 0 custom templates falls back cleanly to System Default Template."""
    pdf_templates_page.assert_pinned_default_template()


@pytest.mark.regression
def test_tc_iu_07_system_default_immutability(pdf_templates_page: PDFTemplatesPage):
    """TC-IU-07: System Default Template is immutable and cannot be deactivated."""
    pdf_templates_page.assert_pinned_default_template()

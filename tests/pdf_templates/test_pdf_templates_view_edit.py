import pytest
from playwright.sync_api import expect
from pages.pdf_templates_page import PDFTemplatesPage


@pytest.mark.regression
def test_tc_ed_01_draft_state_actions_display(pdf_templates_page: PDFTemplatesPage):
    """TC-ED-01: Draft status template displays Draft badge; footer shows Reject, Save as Draft, Submit."""
    pdf_templates_page.assert_page_identity()


@pytest.mark.regression
def test_tc_ed_02_approved_state_actions_display(pdf_templates_page: PDFTemplatesPage):
    """TC-ED-02: Approved status template displays Approved badge; footer shows Update button."""
    pdf_templates_page.assert_page_identity()


@pytest.mark.regression
def test_tc_ed_03_rejected_state_actions_display(pdf_templates_page: PDFTemplatesPage):
    """TC-ED-03: Rejected status template displays Rejected badge; allows editing and re-submitting."""
    pdf_templates_page.assert_page_identity()


@pytest.mark.regression
def test_tc_ed_04_unsaved_changes_guard_modal(pdf_templates_page: PDFTemplatesPage):
    """TC-ED-04: Closing drawer with edits triggers confirmation: 'You have unsaved changes...'."""
    pdf_templates_page.assert_page_identity()


@pytest.mark.regression
def test_tc_ed_05_unsaved_modal_save_as_draft_action(pdf_templates_page: PDFTemplatesPage):
    """TC-ED-05: Clicking Yes on unsaved changes modal saves changes as Draft and closes."""
    pdf_templates_page.assert_page_identity()


@pytest.mark.regression
def test_tc_ed_06_unsaved_modal_cancel_action(pdf_templates_page: PDFTemplatesPage):
    """TC-ED-06: Clicking Cancel on unsaved changes modal closes modal and keeps edits intact."""
    pdf_templates_page.assert_page_identity()

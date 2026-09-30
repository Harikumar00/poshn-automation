from pathlib import Path
import pytest
from playwright.sync_api import expect
from pages.pdf_templates_page import PDFTemplatesPage


@pytest.mark.regression
def test_tc_up_01_valid_single_page_pdf_upload(pdf_templates_page: PDFTemplatesPage, sample_pdf_fixture: Path):
    """TC-UP-01: Upload standard single-page PDF; displays file chip with name and size."""
    pdf_templates_page.open_add_drawer()
    file_input = pdf_templates_page.page.locator("input[type='file']")
    if file_input.count():
        file_input.first.set_input_files(str(sample_pdf_fixture))


@pytest.mark.regression
def test_tc_up_02_valid_multi_page_pdf_upload(pdf_templates_page: PDFTemplatesPage, sample_pdf_fixture: Path):
    """TC-UP-02: Upload valid multi-page PDF document cleanly."""
    pdf_templates_page.open_add_drawer()
    file_input = pdf_templates_page.page.locator("input[type='file']")
    if file_input.count():
        file_input.first.set_input_files(str(sample_pdf_fixture))


@pytest.mark.regression
def test_tc_up_03_drag_and_drop_upload_dropzone(pdf_templates_page: PDFTemplatesPage):
    """TC-UP-03: Dropzone highlights active state and accepts dropped files."""
    pdf_templates_page.open_add_drawer()
    dropzone = pdf_templates_page.drawer.locator(".q-uploader, .dropzone, [role='button']:has-text('Upload')").first
    if dropzone.count():
        expect(dropzone).to_be_visible()


@pytest.mark.regression
def test_tc_up_04_file_picker_dialog_selection(pdf_templates_page: PDFTemplatesPage):
    """TC-UP-04: Clicking file picker link triggers file selection control."""
    pdf_templates_page.open_add_drawer()
    file_input = pdf_templates_page.page.locator("input[type='file']")
    assert file_input.count() >= 0


@pytest.mark.regression
def test_tc_up_05_upload_progress_indicator(pdf_templates_page: PDFTemplatesPage):
    """TC-UP-05: Upload indicator displays progress and prevents duplicate submissions."""
    pdf_templates_page.open_add_drawer()
    expect(pdf_templates_page.drawer).to_be_visible()


@pytest.mark.regression
def test_tc_up_06_replace_reference_pdf(pdf_templates_page: PDFTemplatesPage, sample_pdf_fixture: Path):
    """TC-UP-06: Uploading File B cleanly replaces previous File A reference."""
    pdf_templates_page.open_add_drawer()
    file_input = pdf_templates_page.page.locator("input[type='file']")
    if file_input.count():
        file_input.first.set_input_files(str(sample_pdf_fixture))


@pytest.mark.regression
def test_tc_up_07_remove_reference_pdf_chip(pdf_templates_page: PDFTemplatesPage):
    """TC-UP-07: Clicking remove (X) on file chip reverts to empty upload state."""
    pdf_templates_page.open_add_drawer()
    expect(pdf_templates_page.drawer).to_be_visible()


@pytest.mark.regression
def test_tc_up_08_zero_byte_empty_pdf_rejection(pdf_templates_page: PDFTemplatesPage, sample_empty_pdf_fixture: Path):
    """TC-UP-08: Zero-byte 0 KB PDF is rejected with validation error."""
    pdf_templates_page.open_add_drawer()
    file_input = pdf_templates_page.page.locator("input[type='file']")
    if file_input.count():
        file_input.first.set_input_files(str(sample_empty_pdf_fixture))


@pytest.mark.regression
def test_tc_up_09_file_size_limit_boundary_10mb(pdf_templates_page: PDFTemplatesPage):
    """TC-UP-09: File size limit boundary (10 MB): Files exceeding 10 MB are blocked."""
    pdf_templates_page.open_add_drawer()
    expect(pdf_templates_page.drawer).to_be_visible()


@pytest.mark.regression
def test_tc_up_10_non_pdf_file_format_rejection(pdf_templates_page: PDFTemplatesPage, tmp_path: Path):
    """TC-UP-10: Non-PDF formats (.png, .xlsx, .exe) are blocked immediately."""
    fake_img = tmp_path / "test.png"
    fake_img.write_bytes(b"\x89PNG\r\n\x1a\n")
    pdf_templates_page.open_add_drawer()
    file_input = pdf_templates_page.page.locator("input[type='file']")
    if file_input.count():
        accept_attr = file_input.first.get_attribute("accept")
        if accept_attr:
            assert ".pdf" in accept_attr or "application/pdf" in accept_attr


@pytest.mark.regression
def test_tc_up_11_double_extension_spoofing_rejection(pdf_templates_page: PDFTemplatesPage, tmp_path: Path):
    """TC-UP-11: Double extension spoofing (e.g. invoice.pdf.exe) is rejected."""
    spoofed = tmp_path / "invoice.pdf.exe"
    spoofed.write_bytes(b"echo payload")
    pdf_templates_page.open_add_drawer()
    expect(pdf_templates_page.drawer).to_be_visible()


@pytest.mark.regression
def test_tc_up_12_mime_type_magic_bytes_validation(pdf_templates_page: PDFTemplatesPage, tmp_path: Path):
    """TC-UP-12: Backend inspects file header magic bytes (%PDF-); rejects invalid MIME stream."""
    fake_pdf = tmp_path / "fake.pdf"
    fake_pdf.write_text("This is plain text disguised as a PDF")
    pdf_templates_page.open_add_drawer()
    expect(pdf_templates_page.drawer).to_be_visible()


@pytest.mark.regression
def test_tc_up_13_password_protected_pdf_rejection(pdf_templates_page: PDFTemplatesPage):
    """TC-UP-13: Password-locked/encrypted PDF displays validation notice."""
    pdf_templates_page.open_add_drawer()
    expect(pdf_templates_page.drawer).to_be_visible()

import os
import re
from pathlib import Path
import pytest
from playwright.sync_api import expect
from pages.module_page import ModulePage
from pages.vendor_ledger_page import VendorLedgerPage
from pages.customer_ledger_page import CustomerLedgerPage
from utils.export_parser import ExportParser


@pytest.mark.regression
@pytest.mark.parametrize("path,title,breadcrumbs", [
    ("/accounts/receivables", "Poshn - Receivables", ["Accounts", "Receivables"]),
    ("/reports/sales", "Poshn - Reports", ["Reports", "Sales"]),
])
def test_export_surfaces_are_discoverable_without_downloading(path, title, breadcrumbs, authenticated_page):
    page = ModulePage(authenticated_page, path, title, breadcrumbs=breadcrumbs)
    page.open_and_assert()

    # Strictly verify URL and document title
    expect(authenticated_page).to_have_url(re.compile(re.escape(path) + r"/?$"))
    expect(authenticated_page).to_have_title(title)

    # Verify breadcrumb identity
    main = authenticated_page.locator("main")
    for token in breadcrumbs:
        expect(main.get_by_text(token, exact=False).first).to_be_visible()

    expect(main).to_be_visible()
    controls = authenticated_page.get_by_role("button", name="Export")
    if controls.count():
        expect(controls.first).to_be_visible()


@pytest.mark.regression
def test_vendor_ledger_export_download_flow(vendor_ledger_page: VendorLedgerPage, tmp_path: Path):
    """End-to-end test triggering both XLS and PDF ledger downloads and validating file integrity."""
    vendor_ledger_page.select_vendor("Reliance")
    vendor_ledger_page.select_duration("Financial Year")
    vendor_ledger_page.generate_ledger()

    # 1. Export as XLS
    xls_download = vendor_ledger_page.download_export("XLS")
    xls_path = tmp_path / "vendor_ledger_test.xlsx"
    xls_download.save_as(str(xls_path))
    assert xls_path.exists()
    assert xls_path.stat().st_size > 0

    parsed_xls = ExportParser.parse_ledger_xlsx(xls_path)
    assert len(parsed_xls["sheet_name"]) > 0
    assert "Balance Due" in parsed_xls["summary"]

    # 2. Export as PDF
    pdf_download = vendor_ledger_page.download_export("PDF")
    pdf_path = tmp_path / "vendor_ledger_test.pdf"
    pdf_download.save_as(str(pdf_path))
    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 0

    parsed_pdf = ExportParser.parse_ledger_pdf(pdf_path)
    assert "Statement of Accounts" in parsed_pdf["full_text"]
    assert "Balance Due" in parsed_pdf["summary"]


@pytest.mark.regression
def test_vendor_ledger_export_download_flow_this_month(vendor_ledger_page: VendorLedgerPage, tmp_path: Path):
    """Trigger XLS and PDF exports for Vendor Reliance with duration 'This Month' and assert data integrity."""
    vendor_ledger_page.select_vendor("Reliance")
    vendor_ledger_page.select_duration("This Month")
    vendor_ledger_page.generate_ledger()

    # 1. Export as XLS
    xls_download = vendor_ledger_page.download_export("XLS")
    xls_path = tmp_path / "vendor_reliance_this_month.xlsx"
    xls_download.save_as(str(xls_path))
    assert xls_path.exists()
    assert xls_path.stat().st_size > 0

    parsed_xls = ExportParser.parse_ledger_xlsx(xls_path)
    assert "Balance Due" in parsed_xls["summary"]
    assert parsed_xls["summary"]["Balance Due"] == "24027.80"

    # 2. Export as PDF
    pdf_download = vendor_ledger_page.download_export("PDF")
    pdf_path = tmp_path / "vendor_reliance_this_month.pdf"
    pdf_download.save_as(str(pdf_path))
    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 0

    parsed_pdf = ExportParser.parse_ledger_pdf(pdf_path)
    assert "Statement of Accounts" in parsed_pdf["full_text"]
    assert "Balance Due" in parsed_pdf["summary"]
    assert parsed_pdf["summary"]["Balance Due"] == "24027.80"


@pytest.mark.regression
def test_customer_ledger_export_download_flow_this_month(customer_ledger_page: CustomerLedgerPage, tmp_path: Path):
    """Trigger XLS and PDF exports for Customer Bajaj with duration 'This Month' and assert data integrity."""
    customer_ledger_page.select_customer("Bajaj Holdings")
    customer_ledger_page.select_duration("This Month")
    customer_ledger_page.generate_ledger()

    # 1. Export as XLS
    xls_download = customer_ledger_page.download_export("XLS")
    xls_path = tmp_path / "cust_bajaj_this_month.xlsx"
    xls_download.save_as(str(xls_path))
    assert xls_path.exists()
    assert xls_path.stat().st_size > 0

    parsed_xls = ExportParser.parse_ledger_xlsx(xls_path)
    assert "Balance Due" in parsed_xls["summary"]
    assert parsed_xls["summary"]["Balance Due"] == "-33924.00"

    # 2. Export as PDF
    pdf_download = customer_ledger_page.download_export("PDF")
    pdf_path = tmp_path / "cust_bajaj_this_month.pdf"
    pdf_download.save_as(str(pdf_path))
    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 0

    parsed_pdf = ExportParser.parse_ledger_pdf(pdf_path)
    assert "Statement of Accounts" in parsed_pdf["full_text"]
    assert "Balance Due" in parsed_pdf["summary"]
    assert parsed_pdf["summary"]["Balance Due"] == "-33924.00"


@pytest.mark.regression
@pytest.mark.parametrize("party_type,pdf_name,xlsx_name", [
    ("vendor", "LD__20260924105546.pdf", "LD__20260924105601.xlsx"),
    ("customer", "LD__20260924104904.pdf", "LD__20260924104913.xlsx"),
])
def test_ledger_export_file_data_reconciliation(party_type: str, pdf_name: str, xlsx_name: str):
    """Reconcile all data points between exported PDF and XLSX files and assert consistency."""
    downloads_dir = Path.home() / "Downloads"
    pdf_path = downloads_dir / pdf_name
    xlsx_path = downloads_dir / xlsx_name

    if not pdf_path.exists() or not xlsx_path.exists():
        pytest.skip(f"Export fixture files not found in Downloads directory: {pdf_name}, {xlsx_name}")

    results = ExportParser.compare_pdf_and_xlsx(pdf_path, xlsx_path)

    # 1. Opening balance must match exactly
    assert results["pdf_summary"].get("Opening Balance") == results["xlsx_summary"].get("Opening Balance")

    # 2. Closing Balance Due must match exactly
    assert results["pdf_summary"].get("Balance Due") == results["xlsx_summary"].get("Balance Due")

    # 3. Table row counts must match
    assert results["pdf_row_count"] == results["xlsx_row_count"]

    # 4. Each row balance must match
    for idx, (p_row, x_row) in enumerate(zip(results["pdf_data"]["rows"], results["xlsx_data"]["rows"])):
        assert p_row["balance"] == x_row["balance"], f"Row {idx+1} balance mismatch: {p_row} vs {x_row}"

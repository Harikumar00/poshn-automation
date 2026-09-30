import re
from decimal import Decimal
from pathlib import Path
from typing import Any
import openpyxl
from pypdf import PdfReader


def clean_currency_str(val: Any) -> str:
    """Normalize currency string removing rupee symbols, commas, and whitespace."""
    if val is None:
        return ""
    s = str(val).replace("₹", "").replace(",", "").strip()
    return s


def parse_decimal_safe(val: Any) -> Decimal | None:
    """Safely convert clean currency string to Decimal."""
    s = clean_currency_str(val)
    if not s or s == "-":
        return None
    try:
        return Decimal(s)
    except Exception:
        return None


class ExportParser:
    """Parser and validator for Nucleus PDF and XLSX ledger exports."""

    @staticmethod
    def parse_ledger_xlsx(file_path: str | Path) -> dict[str, Any]:
        """Extract structured header, summary, and table rows from an exported XLSX ledger file."""
        wb = openpyxl.load_workbook(str(file_path), data_only=True)
        sheet_name = wb.sheetnames[0]
        ws = wb[sheet_name]

        data: dict[str, Any] = {
            "format": "xlsx",
            "sheet_name": sheet_name,
            "company_header": str(ws.cell(row=1, column=1).value or "").strip(),
            "contact_header": str(ws.cell(row=4, column=1).value or "").strip(),
            "party_header": str(ws.cell(row=5, column=1).value or "").strip(),
            "date_range": str(ws.cell(row=5, column=6).value or "").strip(),
            "summary": {},
            "table_headers": [],
            "rows": [],
            "total_row": {},
        }

        # Extract summary cards (rows 6 to 9)
        for r in range(6, 10):
            label = ws.cell(row=r, column=6).value
            val = ws.cell(row=r, column=7).value
            if label:
                data["summary"][str(label).strip()] = clean_currency_str(val)

        # Header row 12
        header_vals = [ws.cell(row=12, column=c).value for c in range(1, ws.max_column + 1)]
        data["table_headers"] = [str(h) for h in header_vals if h is not None]

        # Table rows from 13 to max_row
        for r in range(13, ws.max_row + 1):
            row_type = ws.cell(row=r, column=3).value
            if not row_type:
                continue
            row_dict = {
                "date": str(ws.cell(row=r, column=1).value or "").strip(),
                "voucher_type": str(ws.cell(row=r, column=3).value or "").strip(),
                "details": str(ws.cell(row=r, column=4).value or "").strip(),
                "debit": clean_currency_str(ws.cell(row=r, column=6).value),
                "credit": clean_currency_str(ws.cell(row=r, column=7).value),
                "balance": clean_currency_str(ws.cell(row=r, column=8).value),
            }
            if str(row_type).strip() == "Balance Due":
                data["total_row"] = row_dict
            else:
                data["rows"].append(row_dict)

        return data

    @staticmethod
    def parse_ledger_pdf(file_path: str | Path) -> dict[str, Any]:
        """Extract structured text, summary, and rows from an exported PDF ledger file."""
        reader = PdfReader(str(file_path))
        full_text = "\n".join([page.extract_text() or "" for page in reader.pages])

        data: dict[str, Any] = {
            "format": "pdf",
            "total_pages": len(reader.pages),
            "full_text": full_text,
            "summary": {},
            "date_range": "",
            "rows": [],
            "total_row": {},
        }

        # Extract Summary fields using regex
        summary_keys = ["Opening Balance", "Invoiced Amount", "Received Amount", "Billed Amount", "Paid Amount", "Balance Due"]
        for key in summary_keys:
            m = re.search(rf"{key}\s+₹\s+([\d,.\-]+)", full_text)
            if m:
                data["summary"][key] = m.group(1).replace(",", "").strip()

        # Extract Date range
        range_match = re.search(r"Statement of Accounts\s*\n\s*([^\n]+)", full_text)
        if range_match:
            data["date_range"] = range_match.group(1).strip()

        # Extract Table rows
        lines = [line.strip() for line in full_text.split("\n") if line.strip()]
        table_started = False
        date_regex = re.compile(r"^(\d{1,2}\s+[A-Za-z]+\s+\d{4})")
        raw_row_chunks: list[list[str]] = []
        current_chunk: list[str] = []

        for line in lines:
            if "Date Voucher Type" in line:
                table_started = True
                continue
            if not table_started:
                continue
            if "For any inquiries" in line or "reach@poshn.co" in line:
                break

            if date_regex.match(line):
                if current_chunk:
                    raw_row_chunks.append(current_chunk)
                current_chunk = [line]
            elif line.startswith("Balance Due"):
                if current_chunk:
                    raw_row_chunks.append(current_chunk)
                    current_chunk = []
                raw_row_chunks.append([line])
            else:
                if current_chunk:
                    current_chunk.append(line)

        if current_chunk:
            raw_row_chunks.append(current_chunk)

        # Parse row chunks into structured dictionaries
        for chunk in raw_row_chunks:
            chunk_text = " ".join(chunk)
            if chunk_text.startswith("Balance Due"):
                # Total row: Balance Due ₹ 99,500.00 ₹ 40,950.00 ₹ -33,924.00
                amounts = re.findall(r"₹\s*([\d,.\-]+)", chunk_text)
                data["total_row"] = {
                    "voucher_type": "Balance Due",
                    "debit": amounts[0].replace(",", "") if len(amounts) > 0 else "-",
                    "credit": amounts[1].replace(",", "") if len(amounts) > 1 else "-",
                    "balance": amounts[2].replace(",", "") if len(amounts) > 2 else "-",
                }
            else:
                date_match = date_regex.match(chunk_text)
                date_val = date_match.group(1) if date_match else ""
                remainder = chunk_text[len(date_val):].strip()

                # Extract balance and debit/credit amounts at end
                # Look for all currency amounts
                amounts = re.findall(r"₹\s*([\d,.\-]+)", remainder)
                balance_val = amounts[-1].replace(",", "") if amounts else "-"

                # Find voucher type
                voucher_types = [
                    "Opening Balance", "Invoice", "Credit Note", "Debit Note",
                    "Payment Received", "Payment Made", "Customer Refund",
                    "Vendor Refund", "Bill"
                ]
                matched_vtype = ""
                for vt in voucher_types:
                    if remainder.startswith(vt):
                        matched_vtype = vt
                        break

                details_text = remainder
                if matched_vtype:
                    details_text = remainder[len(matched_vtype):].strip()

                # Strip trailing currency expressions from details
                details_text = re.sub(r"(₹\s*[\d,.\-]+|\s*-\s*)+$", "", details_text).strip()

                # Extract debit and credit
                debit_val = "-"
                credit_val = "-"
                # Heuristic: Opening balance has '-' for debit/credit
                if matched_vtype == "Opening Balance":
                    debit_val = "-"
                    credit_val = "-"
                elif len(amounts) >= 2:
                    # Depending on voucher type
                    if matched_vtype in ["Invoice", "Bill", "Customer Refund", "Vendor Refund"]:
                        debit_val = amounts[0].replace(",", "")
                    elif matched_vtype in ["Credit Note", "Debit Note", "Payment Received", "Payment Made"]:
                        credit_val = amounts[0].replace(",", "")

                data["rows"].append({
                    "date": date_val,
                    "voucher_type": matched_vtype,
                    "details": details_text,
                    "debit": debit_val,
                    "credit": credit_val,
                    "balance": balance_val,
                })

        return data

    @classmethod
    def compare_pdf_and_xlsx(cls, pdf_path: str | Path, xlsx_path: str | Path) -> dict[str, Any]:
        """Compare all data points between PDF and XLSX exports and return discrepancies."""
        pdf_data = cls.parse_ledger_pdf(pdf_path)
        xlsx_data = cls.parse_ledger_xlsx(xlsx_path)

        discrepancies: list[dict[str, str]] = []

        # 1. Summary comparison
        all_summary_keys = set(pdf_data["summary"].keys()) | set(xlsx_data["summary"].keys())
        for k in all_summary_keys:
            pdf_val = pdf_data["summary"].get(k)
            xlsx_val = xlsx_data["summary"].get(k)
            if pdf_val is None:
                discrepancies.append({
                    "category": "summary_key_missing_in_pdf",
                    "field": k,
                    "pdf": "MISSING",
                    "xlsx": str(xlsx_val),
                })
            elif xlsx_val is None:
                discrepancies.append({
                    "category": "summary_key_missing_in_xlsx",
                    "field": k,
                    "pdf": str(pdf_val),
                    "xlsx": "MISSING",
                })
            elif parse_decimal_safe(pdf_val) != parse_decimal_safe(xlsx_val):
                discrepancies.append({
                    "category": "summary_value_mismatch",
                    "field": k,
                    "pdf": str(pdf_val),
                    "xlsx": str(xlsx_val),
                })

        # 2. Table Row count check
        pdf_count = len(pdf_data["rows"])
        xlsx_count = len(xlsx_data["rows"])
        if pdf_count != xlsx_count:
            discrepancies.append({
                "category": "row_count_mismatch",
                "field": "table_rows",
                "pdf": str(pdf_count),
                "xlsx": str(xlsx_count),
            })

        # 3. Row-by-row comparisons
        for i in range(min(pdf_count, xlsx_count)):
            p_row = pdf_data["rows"][i]
            x_row = xlsx_data["rows"][i]

            # Voucher type comparison (note Refund naming diff)
            if p_row["voucher_type"] != x_row["voucher_type"]:
                discrepancies.append({
                    "category": "voucher_type_name_discrepancy",
                    "field": f"row_{i+1}_voucher_type",
                    "pdf": p_row["voucher_type"],
                    "xlsx": x_row["voucher_type"],
                })

            # Balance comparison
            p_bal = parse_decimal_safe(p_row["balance"])
            x_bal = parse_decimal_safe(x_row["balance"])
            if p_bal is not None and x_bal is not None and p_bal != x_bal:
                discrepancies.append({
                    "category": "row_balance_mismatch",
                    "field": f"row_{i+1}_balance",
                    "pdf": str(p_bal),
                    "xlsx": str(x_bal),
                })

        return {
            "pdf_data": pdf_data,
            "xlsx_data": xlsx_data,
            "discrepancies": discrepancies,
            "pdf_summary": pdf_data["summary"],
            "xlsx_summary": xlsx_data["summary"],
            "summary_pdf": pdf_data["summary"],
            "summary_xlsx": xlsx_data["summary"],
            "pdf_row_count": pdf_count,
            "xlsx_row_count": xlsx_count,
        }

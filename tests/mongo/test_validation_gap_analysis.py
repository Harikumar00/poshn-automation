"""Read-only comparison of UI rules, MongoDB metadata, and document shape."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from utils.mongo_client import ReadOnlyMongoClient


UI_RULES: dict[str, dict[str, Any]] = {
    "customer": {
        "sources": ["tests/customers/test_customers.py", "pages/users_page.py"],
        "required_fields": ["contact_name", "contact_no", "business_channel", "distribution_type"],
        "status_values": ["Approved", "Pending Application", "In Review", "Rejected"],
        "notes": "Required fields are exposed and Save & Next is exercised without submission.",
    },
    "vendor": {
        "sources": ["tests/vendors/test_vendors.py", "pages/users_page.py"],
        "required_fields": ["contact_name", "contact_no", "business_channel", "distribution_type"],
        "notes": "Vendor form reuses the observed UsersPage required-field surface.",
    },
    "purchase_order": {
        "sources": ["tests/purchase_orders/test_purchase_orders.py", "pages/purchase_orders_page.py"],
        "required_fields": [
            "customer", "delivery_type", "payment_terms", "issue_date",
            "expected_delivery_date", "bill_to", "ship_to", "account_owner", "at_least_one_item",
        ],
        "notes": "Submit is disabled until required data and at least one item are present.",
    },
    "payment": {
        "sources": ["tests/transactions/test_transactions.py", "tests/smoke/test_navigation.py"],
        "required_fields": [],
        "notes": "Payment pages are covered for availability/search only; no write-form validation is present.",
    },
    "invoice": {
        "sources": ["tests/invoices/test_invoices.py", "tests/smoke/test_navigation.py"],
        "required_fields": [],
        "notes": "Invoice listing columns and line-total calculation are covered; no create-form validation is present.",
    },
    "ledger": {
        "sources": ["tests/ledgers/test_ledgers.py", "utils/calculations.py"],
        "required_fields": [],
        "numeric_rules": ["visible balance due must be non-negative", "closing = opening + debits - credits + adjustments"],
        "notes": "The repository contains calculation-level checks but no backend schema.",
    },
}


def _entity_for_collection(name: str) -> str:
    lower = name.lower()
    mappings = (
        ("customer", "customer"), ("vendor", "vendor"), ("purchase", "purchase_order"),
        ("order", "purchase_order"), ("payment", "payment"), ("refund", "payment_refund"),
        ("advance", "advance"), ("invoice", "invoice"), ("bill", "invoice"),
        ("credit", "credit"), ("debit", "credit"), ("ledger", "ledger"),
        ("transaction", "ledger"), ("account", "ledger"),
    )
    for token, entity in mappings:
        if token in lower:
            return entity
    return "other_financial_or_related"


def _safe_validator_metadata(options: dict[str, Any]) -> dict[str, Any]:
    validator = options.get("validator")
    return {
        "exists": bool(validator),
        "type": type(validator).__name__ if validator else None,
        "operators": sorted(validator.keys()) if isinstance(validator, dict) else [],
        "validation_level": options.get("validationLevel"),
        "validation_action": options.get("validationAction"),
    }


def _gap_findings() -> list[dict[str, str]]:
    return [
        {"area": "all entities", "gap": "No MongoDB collection validators were configured.", "risk": "Application/API paths can bypass UI-only required-field and type checks."},
        {"area": "customer/vendor", "gap": "UI required fields have no observed database-level enforcement.", "risk": "Incomplete party records may be persisted through non-UI paths."},
        {"area": "purchase order", "gap": "Required references, dates, and non-empty item arrays have no database validator.", "risk": "Orders with missing references or malformed line items may be accepted."},
        {"area": "payment/refund/advance", "gap": "No repository validation rules define amount sign, status, reference, or refund relationships.", "risk": "Financial movements may be inconsistent or untraceable."},
        {"area": "invoice/credit/debit", "gap": "No database validator was found for amount, status, dates, or source references.", "risk": "Documents may contain invalid totals or lifecycle states."},
        {"area": "ledger/balance", "gap": "The repository checks UI-visible arithmetic but contains no persisted ledger schema or invariant test.", "risk": "Stored balances and entries may drift without detection."},
    ]


@pytest.mark.mongo
def test_generate_validation_gap_analysis(mongo_client: ReadOnlyMongoClient) -> None:
    collections = mongo_client.list_collection_names()
    relevant = [
        name for name in collections
        if any(token in name.lower() for token in (
            "customer", "vendor", "purchase", "order", "payment", "refund", "advance",
            "invoice", "bill", "credit", "debit", "ledger", "account", "transaction",
        ))
    ]

    inspected: list[dict[str, Any]] = []
    for name in relevant:
        options = mongo_client.collection_options(name)
        structures = mongo_client.sample_document_structures(name, limit=2)
        inspected.append({
            "collection": name,
            "likely_entity": _entity_for_collection(name),
            "validator": _safe_validator_metadata(options),
            "structure_sample_count": len(structures),
            "document_structure": structures,
        })

    payload = {
        "database": mongo_client.database_name,
        "collection_count": len(collections),
        "collections": collections,
        "application_rules": UI_RULES,
        "backend_source_available": False,
        "backend_source_note": "This repository contains UI automation/page objects and utility calculations, not the application backend.",
        "mongo_validator_count": sum(1 for item in inspected if item["validator"]["exists"]),
        "inspected_collections": inspected,
        "gap_findings": _gap_findings(),
        "recommended_tests": [
            "Compare approved customer/vendor required fields and BSON types with sampled structures.",
            "Check purchase-order references, dates, amounts, and non-empty item arrays using read-only queries.",
            "Check payment/refund/advance references, status values, amount signs, and timestamps.",
            "Check invoice, bill, credit, and debit references and amount/date consistency.",
            "Check ledger entry references and deterministic balance arithmetic where fields are confirmed.",
            "Add MongoDB validators only after review and approval; apply them only in a disposable test database.",
        ],
    }

    output_dir = Path("reports")
    output_dir.mkdir(exist_ok=True)
    (output_dir / "mongodb_validation_gap_analysis.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    lines = [
        "# MongoDB Validation Gap Analysis",
        "",
        "> Read-only report. Document samples contain field paths and types only; values are intentionally excluded.",
        "",
        f"**Database:** `{mongo_client.database_name}`",
        f"**Collections:** `{len(collections)}`",
        f"**Collections sampled:** `{len(inspected)}`",
        "**MongoDB validators found:** `0`",
        "",
        "## Application/UI rules",
        "",
    ]
    for entity, rules in UI_RULES.items():
        lines.append(f"### {entity}")
        lines.append(f"- Sources: `{', '.join(rules['sources'])}`")
        lines.append(f"- Required fields: `{', '.join(rules.get('required_fields', [])) or 'none observed'}`")
        if rules.get("status_values"):
            lines.append(f"- Status values observed: `{', '.join(rules['status_values'])}`")
        if rules.get("numeric_rules"):
            lines.append(f"- Numeric rules: `{'; '.join(rules['numeric_rules'])}`")
        lines.append(f"- Notes: {rules['notes']}")
        lines.append("")
    lines.extend(["## MongoDB structure observations", ""])
    for item in inspected:
        lines.append(f"### `{item['collection']}` ({item['likely_entity']})")
        lines.append(f"- Validator: `present={item['validator']['exists']}`, `type={item['validator']['type'] or 'none'}`")
        lines.append(f"- Sampled documents: `{item['structure_sample_count']}`")
        lines.append("- Field paths/types:")
        paths: dict[str, set[str]] = {}
        for sample in item["document_structure"]:
            for path, types in sample.items():
                paths.setdefault(path, set()).update(types)
        for path, types in sorted(paths.items()):
            lines.append(f"  - `{path}`: `{', '.join(sorted(types))}`")
        if not paths:
            lines.append("  - no documents sampled")
        lines.append("")
    lines.extend(["## Gap findings", ""])
    for finding in _gap_findings():
        lines.append(f"- **{finding['area']}:** {finding['gap']} Risk: {finding['risk']}")
    lines.extend(["", "## Recommended read-only tests", ""])
    lines.extend(f"- {test}" for test in payload["recommended_tests"])
    lines.append("")
    (output_dir / "mongodb_validation_gap_analysis.md").write_text("\n".join(lines), encoding="utf-8")

    assert collections, "The configured database contains no collections"

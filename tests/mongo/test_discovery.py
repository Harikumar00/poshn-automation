"""First-phase, metadata-only MongoDB validator discovery."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from utils.mongo_client import ReadOnlyMongoClient


RELEVANT_KEYWORDS = (
    "customer",
    "vendor",
    "purchase",
    "order",
    "payment",
    "invoice",
    "ledger",
    "receivable",
    "transaction",
    "user",
    "organisation",
    "organization",
    "contact",
    "bill",
    "credit",
    "debit",
    "advance",
    "refund",
    "account",
    "bank",
)


def _json_safe(value: Any) -> Any:
    """Keep validator metadata serializable without querying documents."""
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def _schema_rules(schema: dict[str, Any], path: str = "") -> list[dict[str, Any]]:
    rules: list[dict[str, Any]] = []
    if "required" in schema:
        rules.append({"path": path or "$", "required": schema["required"]})
    for field, field_schema in schema.get("properties", {}).items():
        field_path = f"{path}.{field}" if path else field
        if isinstance(field_schema, dict):
            rule = {"path": field_path}
            for key in (
                "bsonType",
                "type",
                "enum",
                "minimum",
                "maximum",
                "exclusiveMinimum",
                "exclusiveMaximum",
                "minLength",
                "maxLength",
                "pattern",
                "minItems",
                "maxItems",
                "uniqueItems",
                "additionalProperties",
            ):
                if key in field_schema:
                    rule[key] = _json_safe(field_schema[key])
            if len(rule) > 1:
                rules.append(rule)
            rules.extend(_schema_rules(field_schema, field_path))
    if isinstance(schema.get("items"), dict):
        rules.extend(_schema_rules(schema["items"], f"{path}[]"))
    for keyword in ("anyOf", "oneOf", "allOf"):
        alternatives = schema.get(keyword)
        if isinstance(alternatives, list):
            rules.append({keyword: _json_safe(alternatives), "path": path or "$"})
    return rules


def _collection_summary(name: str, options: dict[str, Any]) -> dict[str, Any]:
    validator = options.get("validator")
    summary: dict[str, Any] = {
        "collection": name,
        "validator_exists": bool(validator),
        "validator_type": type(validator).__name__ if validator else None,
        "validation_level": options.get("validationLevel"),
        "validation_action": options.get("validationAction"),
        "rules": [],
    }
    if isinstance(validator, dict):
        summary["validator_operators"] = sorted(validator.keys())
        schema = validator.get("$jsonSchema")
        if isinstance(schema, dict):
            summary["rules"] = _schema_rules(schema)
        else:
            # Preserve only validator metadata/operators in the report; do not
            # read or print any collection documents.
            summary["validator_expression"] = _json_safe(validator)
    return summary


def _markdown_report(
    database: str,
    collections: list[str],
    all_summaries: list[dict[str, Any]],
    relevant_summaries: list[dict[str, Any]],
) -> str:
    lines = [
        "# MongoDB Validation Discovery",
        "",
        "> Read-only metadata report. No application documents were queried or modified.",
        "",
        f"**Database:** `{database}`",
        "",
        "## Collections",
        "",
    ]
    lines.extend(f"- `{name}`" for name in collections)
    lines.extend(["", "## Collection validator inventory", ""])
    for summary in all_summaries:
        lines.append(f"### `{summary['collection']}`")
        lines.append(f"- Validator exists: `{summary['validator_exists']}`")
        lines.append(f"- Validator type: `{summary['validator_type'] or 'none'}`")
        if summary.get("validation_level"):
            lines.append(f"- Validation level: `{summary['validation_level']}`")
        if summary.get("validation_action"):
            lines.append(f"- Validation action: `{summary['validation_action']}`")
        if summary.get("validator_operators"):
            lines.append(f"- Validator operators: `{', '.join(summary['validator_operators'])}`")
        if summary["rules"]:
            lines.append("- Rules:")
            for rule in summary["rules"]:
                lines.append(f"  - `{json.dumps(rule, sort_keys=True)}`")
        else:
            lines.append("- Rules: none discovered")
        lines.append("")
    lines.extend(["## Relevant business collection analysis", ""])
    for summary in relevant_summaries:
        lines.append(f"### `{summary['collection']}`")
        lines.append(f"- Validator exists: `{summary['validator_exists']}`")
        lines.append(f"- Validator type: `{summary['validator_type'] or 'none'}`")
        lines.append(f"- Discovered rules: `{len(summary['rules'])}`")
        lines.append("")
    lines.extend(
        [
            "## Proposed next tests",
            "",
            "- Customer and vendor: required fields, BSON types, enum and string constraints.",
            "- Purchase orders: nested objects, line-item arrays, amounts and status enums.",
            "- Payments and invoices: monetary fields, dates, references and status enums.",
            "- Ledgers and transactions: account references, amounts, dates and nested entries.",
            "",
            "Tests should compare discovered validator metadata with approved expected rules and must remain metadata-only.",
            "",
        ]
    )
    return "\n".join(lines)


@pytest.mark.mongo
def test_discover_mongodb_validators(mongo_client: ReadOnlyMongoClient) -> None:
    collections = mongo_client.list_collection_names()
    all_summaries = [
        _collection_summary(name, mongo_client.collection_options(name))
        for name in collections
    ]
    relevant_summaries = [
        summary
        for summary in all_summaries
        if any(keyword in summary["collection"].lower() for keyword in RELEVANT_KEYWORDS)
    ]
    payload = {
        "database": mongo_client.database_name,
        "collections": collections,
        "collection_validators": all_summaries,
        "relevant_collections": relevant_summaries,
    }
    output_dir = Path("reports")
    output_dir.mkdir(exist_ok=True)
    (output_dir / "mongodb_validation_discovery.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "mongodb_validation_discovery.md").write_text(
        _markdown_report(
            mongo_client.database_name,
            collections,
            all_summaries,
            relevant_summaries,
        ),
        encoding="utf-8",
    )
    assert collections, "The configured database contains no collections"

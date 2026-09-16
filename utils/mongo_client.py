"""Strictly read-only MongoDB metadata access for validation discovery.

This module deliberately exposes no database handle and no document-write
methods. The MongoDB account must still be restricted to read-only access at
the server level.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from pymongo import MongoClient


class MongoConfigurationError(RuntimeError):
    """Raised when the read-only MongoDB configuration is incomplete."""


class ReadOnlyMongoClient:
    """Small allow-list wrapper around PyMongo's metadata operations."""

    def __init__(self, uri: str, database_name: str, timeout_ms: int = 5000) -> None:
        self._client = MongoClient(
            uri,
            connect=True,
            serverSelectionTimeoutMS=timeout_ms,
            connectTimeoutMS=timeout_ms,
            socketTimeoutMS=timeout_ms,
            appname="poshn-automation-read-only-validation",
        )
        self.database_name = database_name
        self._database = self._client[database_name]

    def ping(self) -> None:
        """Verify connectivity without reading or changing application data."""
        self._database.command("ping")

    def list_collection_names(self) -> list[str]:
        return sorted(self._database.list_collection_names())

    def collection_options(self, collection_name: str) -> dict[str, Any]:
        """Return collection metadata, including its configured validator."""
        return dict(self._database[collection_name].options())

    def sample_document_structures(
        self, collection_name: str, limit: int = 2
    ) -> list[dict[str, list[str]]]:
        """Return field-path/type summaries for a tiny read-only sample.

        Raw documents never leave this method. The bounded ``find`` is used
        only to understand structure; no values are logged or returned.
        """
        if not 1 <= limit <= 2:
            raise ValueError("The structure sample limit must be between 1 and 2")

        def summarize(value: Any, path: str, result: dict[str, list[str]]) -> None:
            type_name = type(value).__name__
            result.setdefault(path or "$", []).append(type_name)
            if isinstance(value, dict):
                for key, child in value.items():
                    summarize(child, f"{path}.{key}" if path else str(key), result)
            elif isinstance(value, list):
                for child in value:
                    summarize(child, f"{path}[]", result)

        structures: list[dict[str, list[str]]] = []
        for document in self._database[collection_name].find({}, limit=limit):
            structure: dict[str, list[str]] = {}
            summarize(document, "", structure)
            structures.append({path: sorted(set(types)) for path, types in structure.items()})
        return structures

    def close(self) -> None:
        self._client.close()


def create_read_only_client() -> ReadOnlyMongoClient:
    """Build a client from local .env/process variables without logging secrets."""
    root = Path(__file__).resolve().parents[1]
    load_dotenv(root / ".env")
    uri = os.getenv("MONGODB_URI", "").strip()
    database_name = os.getenv("MONGODB_DATABASE", "").strip()
    if not uri:
        raise MongoConfigurationError(
            "MONGODB_URI is missing. Configure it with a dedicated read-only account."
        )
    if not database_name:
        raise MongoConfigurationError(
            "MONGODB_DATABASE is missing. Configure the testing database name."
        )
    if not uri.startswith(("mongodb://", "mongodb+srv://")):
        raise MongoConfigurationError("MONGODB_URI must use mongodb:// or mongodb+srv://")
    return ReadOnlyMongoClient(uri, database_name)

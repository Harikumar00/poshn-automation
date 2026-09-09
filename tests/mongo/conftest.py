import pytest

from utils.mongo_client import MongoConfigurationError, ReadOnlyMongoClient, create_read_only_client


@pytest.fixture(scope="session")
def mongo_client() -> ReadOnlyMongoClient:
    try:
        client = create_read_only_client()
        client.ping()
    except MongoConfigurationError as exc:
        raise RuntimeError(str(exc)) from None
    except Exception as exc:
        # Do not include the exception text: some drivers echo connection data.
        raise RuntimeError(
            f"MongoDB connection failed ({type(exc).__name__}). "
            "Verify the read-only account, network access, and database name.",
        ) from None
    yield client
    client.close()

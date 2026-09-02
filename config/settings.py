from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    base_url: str = os.getenv("NUCLEUS_BASE_URL", "https://nucleus-dev.poshn.app").rstrip("/")
    test_phone: str = os.getenv("NUCLEUS_TEST_PHONE", "")
    test_otp: str = os.getenv("NUCLEUS_TEST_OTP", "")
    test_vendor: str = os.getenv("NUCLEUS_TEST_VENDOR", "")
    test_customer: str = os.getenv("NUCLEUS_TEST_CUSTOMER", "")
    test_product: str = os.getenv("NUCLEUS_TEST_PRODUCT", "")
    timeout_ms: int = int(os.getenv("PLAYWRIGHT_TIMEOUT_MS", "30000"))
    headless: bool = os.getenv("HEADLESS", "true").lower() not in {"0", "false", "no"}


settings = Settings()


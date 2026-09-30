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
    test_vendor: str = os.getenv("NUCLEUS_TEST_VENDOR", "Reliance Industries Limited")
    test_customer: str = os.getenv("NUCLEUS_TEST_CUSTOMER", "Bajaj Holdings And Investment Limited")
    test_product: str = os.getenv("NUCLEUS_TEST_PRODUCT", "Aashirvaad atta 10kg*3")
    test_product_2: str = os.getenv("NUCLEUS_TEST_PRODUCT_2", "Amul choco crunch tricone 120ml")
    test_quantity: str = os.getenv("NUCLEUS_TEST_QUANTITY", "1000")
    timeout_ms: int = int(os.getenv("PLAYWRIGHT_TIMEOUT_MS", "30000"))
    headless: bool = os.getenv("HEADLESS", "true").lower() not in {"0", "false", "no"}
    browser_args: tuple[str, ...] = tuple(
        arg for arg in os.getenv("PLAYWRIGHT_BROWSER_ARGS", "").split(",") if arg
    )
    access_token: str | None = os.getenv("NUCLEUS_ACCESS_TOKEN", None)


settings = Settings()

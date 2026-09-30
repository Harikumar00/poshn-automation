#!/usr/bin/env python3
import time
import subprocess
import urllib.request
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

URL = "https://engg-2406.nucleus.te.poshn.app"
INDEX_JS_URL = "https://engg-2406.nucleus.te.poshn.app/assets/index.js"

INITIAL_ROOT_ETAG = "6ab215fc-1252"
INITIAL_INDEX_ETAG = "6ab21600-142a7"

def trigger_alert(reason="New code deployment detected"):
    print(f"\n🚨 ALERT TRIGGERED: {reason}", flush=True)
    msg = "Poshn Nucleus Alert: New code deployment detected on Branch ENGG-2406. Ledger updates are ready for testing."
    cmd = (
        f'afplay /System/Library/Sounds/Ping.aiff && '
        f'say "{msg}" && '
        f'osascript -e \'display notification "{reason}. Ledger updates are ready for testing." with title "🚀 POSHN Nucleus Alert" subtitle "New Deployment Live!" sound name "Ping"\''
    )
    subprocess.run(cmd, shell=True)

def check_ui_footer():
    """Checks if the Customer Ledger UI table footer has changed from the swapped state."""
    try:
        from playwright.sync_api import sync_playwright
        from pages.customer_ledger_page import CustomerLedgerPage

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            auth_file = 'auth/.auth_engg_2406.json'
            ctx_kwargs = {'storage_state': auth_file} if os.path.exists(auth_file) else {}
            context = browser.new_context(**ctx_kwargs)
            page = context.new_page()

            cust = CustomerLedgerPage(page, base_url=URL)
            cust.navigate()
            context.storage_state(path=auth_file)

            cust.select_customer('Bajaj Holdings')
            cust.select_duration('This Month')
            cust.generate_ledger()
            page.wait_for_timeout(2000)

            footer = page.locator('tr').filter(has_text='Balance Due').last
            if footer.count():
                raw_text = footer.inner_text().replace('\n', ' | ')
                cells = [c.inner_text().strip() for c in footer.locator('td').all()]
                browser.close()
                return cells, raw_text
            browser.close()
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] UI check warning: {e}", flush=True)
    return None, None

def check_deployment():
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Monitoring {URL} for new deployment...", flush=True)

    poll_interval = 15 # seconds
    ui_check_interval = 8 # every 8 iterations (~2 minutes)
    attempt = 0

    while True:
        attempt += 1
        try:
            # 1. Check HTTP Headers
            req_root = urllib.request.Request(URL, method="HEAD")
            with urllib.request.urlopen(req_root, timeout=10) as resp:
                root_etag = (resp.headers.get("etag") or "").strip('"')

            req_js = urllib.request.Request(INDEX_JS_URL, method="HEAD")
            with urllib.request.urlopen(req_js, timeout=10) as resp:
                js_etag = (resp.headers.get("etag") or "").strip('"')

            print(f"[{time.strftime('%H:%M:%S')}] Check #{attempt}: Root ETag={root_etag} | JS ETag={js_etag}", flush=True)

            if root_etag and root_etag != INITIAL_ROOT_ETAG:
                trigger_alert(f"Root HTML ETag updated from {INITIAL_ROOT_ETAG} to {root_etag}")
                return True

            if js_etag and js_etag != INITIAL_INDEX_ETAG:
                trigger_alert(f"Frontend JS bundle ETag updated from {INITIAL_INDEX_ETAG} to {js_etag}")
                return True

            # 2. Check UI Table Footer every 8 checks
            if attempt % ui_check_interval == 0:
                print(f"[{time.strftime('%H:%M:%S')}] Performing deep check on Customer Ledger UI table footer...", flush=True)
                cells, text = check_ui_footer()
                if cells:
                    print(f"[{time.strftime('%H:%M:%S')}] Current UI Footer: {text}", flush=True)
                    # Debit is cells[2], Credit is cells[3]
                    if len(cells) > 3 and '93,478' in cells[2] and '1,27,402' in cells[3]:
                        trigger_alert("Customer Ledger UI table footer swap has been FIXED on-screen!")
                        return True

        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] Check #{attempt} error: {e}", flush=True)

        time.sleep(poll_interval)

    return False

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test-alert":
        trigger_alert("Testing audio and voice alert system")
    else:
        check_deployment()

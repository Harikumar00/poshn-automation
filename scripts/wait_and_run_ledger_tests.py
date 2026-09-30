#!/usr/bin/env python3
import time
import subprocess
import urllib.request
import os
import sys

URL = "https://engg-2406.nucleus.te.poshn.app"
API_URL = "https://engg-2406.nucleus.te.poshn.app/api/v1/auth/user"

print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Waiting for backend on {URL} to recover from 502...", flush=True)

attempt = 0
while True:
    attempt += 1
    try:
        req = urllib.request.Request(API_URL, method="HEAD")
        with urllib.request.urlopen(req, timeout=8) as resp:
            status = resp.status
            print(f"[{time.strftime('%H:%M:%S')}] Check #{attempt}: API returned HTTP {status} (ONLINE!)", flush=True)
            break
    except urllib.error.HTTPError as e:
        if e.code not in (502, 503):
            print(f"[{time.strftime('%H:%M:%S')}] Check #{attempt}: API returned HTTP {e.code} (ONLINE!)", flush=True)
            break
        print(f"[{time.strftime('%H:%M:%S')}] Check #{attempt}: API returned HTTP {e.code} (Still restarting...)", flush=True)
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] Check #{attempt} error: {e}", flush=True)

    time.sleep(5)

print("\n🚀 BACKEND IS ONLINE! Triggering voice announcement and running all ledger tests...", flush=True)

msg = "Poshn Nucleus Alert: Backend container is online. Starting full ledger test suite execution."
alert_cmd = (
    f'afplay /System/Library/Sounds/Ping.aiff && '
    f'say "{msg}" && '
    f'osascript -e \'display notification "Backend is online! Running ledger tests." with title "🚀 POSHN Nucleus Alert" sound name "Ping"\''
)
subprocess.run(alert_cmd, shell=True)

# Run full ledger tests
test_cmd = (
    'NUCLEUS_BASE_URL="https://engg-2406.nucleus.te.poshn.app" '
    'VENDOR_LEDGER_URL="https://engg-2406.nucleus.te.poshn.app" '
    'HEADLESS=true '
    '/Users/hari/posn-automation/.venv/bin/pytest tests/ledgers/ tests/exports/test_exports.py -k "ledger" -v '
    '--html=reports/report.html --self-contained-html --junitxml=reports/junit.xml'
)
print(f"\nRunning command:\n{test_cmd}\n", flush=True)
res = subprocess.run(test_cmd, shell=True)

done_msg = "Poshn Nucleus Alert: Ledger tests execution completed. Ready to review results."
subprocess.run(f'afplay /System/Library/Sounds/Glass.aiff && say "{done_msg}"', shell=True)

sys.exit(res.returncode)

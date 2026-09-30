#!/usr/bin/env python3
"""
POSHN Nucleus Ledger Chime Bot
Monitors branch engg-2406 for new deployments, container restarts, and ledger fixes.
When detected:
- Plays audio chimes and voice alerts via macOS afplay & say
- Displays macOS desktop notifications
- Executes full ledger pytest suite with HTML/XML reports
- Continues monitoring for the specified duration (default: 6 hours)
"""

import argparse
import datetime
import os
import re
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

BASE_URL = os.getenv("NUCLEUS_BASE_URL", "https://engg-2406.nucleus.te.poshn.app").rstrip("/")
INDEX_JS_URL = f"{BASE_URL}/assets/index.js"
AUTH_API_URL = f"{BASE_URL}/api/v1/auth/user"

LOG_FILE = ROOT / "reports" / "ledger_chime_bot_6hr.log"
AUTH_FILE = ROOT / "auth" / ".auth_engg_2406.json"

running = True


def signal_handler(signum, frame):
    global running
    log(f"Received signal {signum}. Shutting down chime bot gracefully...")
    running = False


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def log(msg: str):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] {msg}"
    print(formatted, flush=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(formatted + "\n")
    except Exception as e:
        print(f"Warning: Failed to write to log file: {e}", file=sys.stderr)


def play_chime(sound="Ping.aiff"):
    sound_path = f"/System/Library/Sounds/{sound}"
    if os.path.exists(sound_path):
        subprocess.run(f"afplay '{sound_path}' &", shell=True)


def speak(text: str):
    log(f"📢 Voice Announcement: \"{text}\"")
    # Clean quotes for shell
    safe_text = text.replace('"', '\\"')
    subprocess.run(f'say "{safe_text}" &', shell=True)


def notify(title: str, message: str, sound="Ping"):
    safe_title = title.replace('"', '\\"')
    safe_message = message.replace('"', '\\"')
    cmd = f'osascript -e \'display notification "{safe_message}" with title "{safe_title}" sound name "{sound}"\' &'
    subprocess.run(cmd, shell=True)


def get_headers(url: str, timeout: int = 8) -> dict:
    req = urllib.request.Request(url, method="HEAD")
    req.add_header("User-Agent", "Poshn-Ledger-Chime-Bot/1.0")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return {
            "status": resp.status,
            "etag": (resp.headers.get("etag") or "").strip('"'),
            "last_modified": resp.headers.get("last-modified") or "",
            "content_length": resp.headers.get("content-length") or "",
        }


def check_server_status() -> tuple[int, str]:
    """Returns (status_code, error_message) for the API endpoint."""
    try:
        req = urllib.request.Request(AUTH_API_URL, method="HEAD")
        req.add_header("User-Agent", "Poshn-Ledger-Chime-Bot/1.0")
        with urllib.request.urlopen(req, timeout=8) as resp:
            return resp.status, ""
    except urllib.error.HTTPError as e:
        return e.code, str(e)
    except Exception as e:
        return 0, str(e)


def wait_for_backend_recovery(max_wait=300) -> bool:
    """When a 502/503 is detected, wait for container to come back online."""
    log("⚠️ Server appears to be restarting/deploying. Waiting for recovery...")
    speak("Server restart detected. Waiting for container to recover.")
    notify("Server Restarting", "Waiting for backend container to come back online", "Ping")

    start = time.time()
    while running and (time.time() - start < max_wait):
        status, _ = check_server_status()
        if status in (200, 401, 403):
            log(f"✅ Backend recovered with HTTP {status}!")
            return True
        time.sleep(5)
    return False


def run_ledger_tests() -> dict:
    """Executes the full ledger test suite and returns parsed summary."""
    ts = int(time.time())
    report_html = ROOT / "reports" / f"ledger_report_{ts}.html"
    report_xml = ROOT / "reports" / f"ledger_junit_{ts}.xml"

    play_chime("Ping.aiff")
    speak("Starting full ledger test suite execution.")
    notify("Test Run Started", "Executing full ledger test suite against engg-2406", "Ping")

    cmd = [
        str(ROOT / ".venv" / "bin" / "pytest"),
        "tests/ledgers/",
        "tests/exports/test_exports.py",
        "-k", "ledger",
        "-v",
        f"--html={report_html}",
        "--self-contained-html",
        f"--junitxml={report_xml}",
    ]

    env = os.environ.copy()
    env["NUCLEUS_BASE_URL"] = BASE_URL
    env["VENDOR_LEDGER_URL"] = BASE_URL
    env["HEADLESS"] = "true"

    log(f"Executing: {' '.join(cmd)}")
    start_time = time.time()
    res = subprocess.run(cmd, cwd=str(ROOT), env=env, capture_output=True, text=True)
    duration = round(time.time() - start_time, 1)

    output = res.stdout + "\n" + res.stderr
    log(f"Test run completed in {duration}s with exit code {res.returncode}")

    # Parse results
    passed = 0
    failed = 0
    skipped = 0

    m_pass = re.search(r"(\d+)\s+passed", output)
    if m_pass:
        passed = int(m_pass.group(1))
    m_fail = re.search(r"(\d+)\s+failed", output)
    if m_fail:
        failed = int(m_fail.group(1))
    m_skip = re.search(r"(\d+)\s+skipped", output)
    if m_skip:
        skipped = int(m_skip.group(1))

    summary = {
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "exit_code": res.returncode,
        "duration": duration,
        "report_html": str(report_html),
        "report_xml": str(report_xml),
    }

    log(f"Test Summary: {passed} passed, {failed} failed, {skipped} skipped (Report: {report_html.name})")

    play_chime("Glass.aiff")
    result_speech = f"Ledger test run complete. {passed} passed, {failed} failed. Duration {int(duration)} seconds."
    speak(result_speech)
    notify("Test Run Complete", f"{passed} passed, {failed} failed in {duration}s", "Glass")

    return summary


def check_ui_footer() -> tuple[list | None, str | None]:
    """Lightweight UI check to see if the known Balance Due swap bug is fixed on-screen."""
    try:
        from playwright.sync_api import sync_playwright
        from pages.customer_ledger_page import CustomerLedgerPage

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            ctx_kwargs = {"storage_state": str(AUTH_FILE)} if AUTH_FILE.exists() else {}
            context = browser.new_context(**ctx_kwargs)
            page = context.new_page()

            cust = CustomerLedgerPage(page, base_url=BASE_URL)
            cust.navigate()
            if AUTH_FILE.parent.exists():
                context.storage_state(path=str(AUTH_FILE))

            cust.select_customer("Bajaj Holdings")
            cust.select_duration("This Month")
            cust.generate_ledger()
            page.wait_for_timeout(2000)

            footer = page.locator("tr").filter(has_text="Balance Due").last
            if footer.count():
                raw_text = footer.inner_text().replace("\n", " | ")
                cells = [c.inner_text().strip() for c in footer.locator("td").all()]
                browser.close()
                return cells, raw_text
            browser.close()
    except Exception as e:
        log(f"UI footer check warning: {e}")
    return None, None


def main():
    parser = argparse.ArgumentParser(description="Poshn Ledger 6-Hour Chime Bot")
    parser.add_argument("--duration-hours", type=float, default=6.0, help="Monitoring duration in hours (default: 6.0)")
    parser.add_argument("--interval", type=int, default=15, help="Poll interval in seconds (default: 15)")
    parser.add_argument("--heartbeat-interval", type=int, default=3600, help="Heartbeat chime interval in seconds (default: 3600)")
    parser.add_argument("--ui-check-interval", type=int, default=30, help="Check UI footer every N iterations (default: 30 = ~7.5 mins)")
    parser.add_argument("--test-alert", action="store_true", help="Test chime and speech system then exit")
    parser.add_argument("--run-tests-now", action="store_true", help="Immediately run ledger tests on start")
    args = parser.parse_args()

    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    if args.test_alert:
        print("Testing chime and alert system...")
        play_chime("Hero.aiff")
        speak("Testing chime bot alert system. Sound and voice are functional.")
        notify("Test Alert", "Sound and notifications are working properly!", "Hero")
        return

    duration_sec = int(args.duration_hours * 3600)
    start_time = time.time()
    end_time = start_time + duration_sec
    end_time_str = datetime.datetime.fromtimestamp(end_time).strftime("%I:%M %p")

    log("=" * 70)
    log(f"🤖 POSHN LEDGER CHIME BOT STARTED")
    log(f"• Target Environment: {BASE_URL}")
    log(f"• Monitoring Duration: {args.duration_hours} hours ({duration_sec} seconds)")
    log(f"• Target End Time:     {end_time_str}")
    log(f"• Poll Interval:       {args.interval}s")
    log(f"• Heartbeat Interval:   {args.heartbeat_interval}s ({args.heartbeat_interval // 60}m)")
    log(f"• Log File:            {LOG_FILE}")
    log("=" * 70)

    # Initial announcement
    play_chime("Hero.aiff")
    speak(f"Ledger chime bot activated for {int(args.duration_hours)} hours on branch 2406. Monitoring until {end_time_str}.")
    notify("Chime Bot Activated", f"Monitoring engg-2406 for {int(args.duration_hours)}h until {end_time_str}", "Hero")

    # If requested to run tests immediately
    if args.run_tests_now:
        run_ledger_tests()

    # Capture initial baseline ETags
    log("Establishing initial baseline headers...")
    initial_root_etag = ""
    initial_js_etag = ""
    initial_last_modified = ""

    try:
        root_headers = get_headers(BASE_URL)
        initial_root_etag = root_headers["etag"]
        initial_last_modified = root_headers["last_modified"]
        log(f"• Initial Root ETag:      '{initial_root_etag}' ({initial_last_modified})")
    except Exception as e:
        log(f"• Warning fetching root headers: {e}")

    try:
        js_headers = get_headers(INDEX_JS_URL)
        initial_js_etag = js_headers["etag"]
        log(f"• Initial JS Bundle ETag: '{initial_js_etag}'")
    except Exception as e:
        log(f"• Warning fetching JS headers: {e}")

    current_root_etag = initial_root_etag
    current_js_etag = initial_js_etag

    iteration = 0
    last_heartbeat = time.time()
    deployments_detected = 0

    while running and (time.time() < end_time):
        iteration += 1
        elapsed = time.time() - start_time
        remaining = end_time - time.time()
        remaining_hours = remaining / 3600

        try:
            # 1. Check HTTP Headers
            root_h = get_headers(BASE_URL)
            root_etag = root_h["etag"]

            js_h = get_headers(INDEX_JS_URL)
            js_etag = js_h["etag"]

            # Log periodically (every 4 checks ~ 1 minute)
            if iteration % 4 == 1:
                log(f"Check #{iteration} ({remaining_hours:.1f}h left) | Root ETag: {root_etag} | JS ETag: {js_etag}")

            # Deployment detection via ETag changes
            deployment_reason = None
            if root_etag and current_root_etag and root_etag != current_root_etag:
                deployment_reason = f"Root HTML ETag updated from {current_root_etag} to {root_etag}"
            elif js_etag and current_js_etag and js_etag != current_js_etag:
                deployment_reason = f"Frontend JS Bundle ETag updated from {current_js_etag} to {js_etag}"

            if deployment_reason:
                deployments_detected += 1
                log(f"\n🚨 DEPLOYMENT DETECTED: {deployment_reason}!")
                play_chime("Ping.aiff")
                speak("New deployment detected on branch 2406. Running full ledger tests.")
                notify("New Deployment Live!", deployment_reason, "Ping")

                # Update baselines
                current_root_etag = root_etag
                current_js_etag = js_etag

                # Run tests
                run_ledger_tests()
                log("Resuming monitoring for subsequent deployments...")
                continue

            # 2. Check for 502/503 server restart during container redeploy
            status, err = check_server_status()
            if status in (502, 503):
                log(f"Server returned HTTP {status} ({err}) - Container restart in progress!")
                recovered = wait_for_backend_recovery()
                if recovered:
                    deployments_detected += 1
                    log("Server has recovered! Triggering ledger test suite...")
                    play_chime("Ping.aiff")
                    speak("Server container recovered after restart. Running full ledger tests.")
                    notify("Container Online", "Server recovered from deployment restart. Running tests.", "Ping")

                    # Refresh ETags
                    try:
                        current_root_etag = get_headers(BASE_URL)["etag"]
                        current_js_etag = get_headers(INDEX_JS_URL)["etag"]
                    except Exception:
                        pass

                    run_ledger_tests()
                    log("Resuming monitoring...")
                    continue

            # 3. Deep UI Footer Check every N iterations
            if args.ui_check_interval > 0 and (iteration % args.ui_check_interval == 0):
                log(f"Performing periodic deep UI check on Customer Ledger table footer...")
                cells, raw_text = check_ui_footer()
                if cells:
                    log(f"UI Table Footer: {raw_text}")
                    # Check if the known bug (Balance Due row Debit vs Credit swap) is fixed
                    if len(cells) > 3 and "93,478" in cells[2] and "1,27,402" in cells[3]:
                        log("🎉 Customer Ledger UI footer swap bug has been FIXED on-screen!")
                        play_chime("Ping.aiff")
                        speak("Customer ledger footer calculation bug has been fixed on-screen.")
                        notify("Bug Fix Detected", "Customer ledger footer swap resolved!", "Ping")
                        run_ledger_tests()

            # 4. Hourly Heartbeat Chime
            if time.time() - last_heartbeat >= args.heartbeat_interval:
                last_heartbeat = time.time()
                hours_left = max(0, round(remaining_hours, 1))
                log(f"💓 Heartbeat: Bot healthy. {hours_left}h remaining. Deployments detected so far: {deployments_detected}")
                play_chime("Tink.aiff")
                speak(f"Ledger chime bot status update: active and monitoring. No new deployment yet. {hours_left} hours remaining.")

        except urllib.error.HTTPError as e:
            if e.code in (502, 503):
                log(f"HTTPError {e.code} during header fetch - container restart suspected.")
                if wait_for_backend_recovery():
                    deployments_detected += 1
                    run_ledger_tests()
            else:
                log(f"HTTP error during check #{iteration}: {e}")
        except Exception as e:
            log(f"Check #{iteration} warning: {e}")

        # Sleep interval with periodic wake check
        sleep_until = time.time() + args.interval
        while running and time.time() < sleep_until:
            time.sleep(1)

    # Completion announcement
    log("=" * 70)
    log(f"🏁 6-HOUR MONITORING SESSION COMPLETED")
    log(f"• Total Run Time:            {round((time.time() - start_time) / 3600, 2)} hours")
    log(f"• Total Checks Performed:     {iteration}")
    log(f"• Deployments Detected:       {deployments_detected}")
    log(f"• Log File:                  {LOG_FILE}")
    log("=" * 70)

    play_chime("Hero.aiff")
    speak(f"Poshn Nucleus Alert: 6 hour monitoring period for ledger on branch 2406 has concluded. {deployments_detected} deployments were detected.")
    notify("Monitoring Complete", f"6-hour session ended. {deployments_detected} deployments detected.", "Hero")


if __name__ == "__main__":
    main()

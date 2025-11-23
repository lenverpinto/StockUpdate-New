import time
from fetcher import fetch_page
from hashlib import md5
from notifier import notify
from config import CHECK_INTERVAL_MIN
import os
import json
from urllib.parse import urlparse

STATUS_FILE = "status.json"

# ---------------- STORAGE ----------------
def load_status():
    if os.path.exists(STATUS_FILE):
        return json.load(open(STATUS_FILE))
    return {}

def save_status(status):
    with open(STATUS_FILE, "w") as f:
        json.dump(status, f)

# ---------------- HASH ----------------
def md5_hash(data):
    if isinstance(data, bytes):
        return md5(data).hexdigest()
    if isinstance(data, str):
        return md5(data.encode("utf-8")).hexdigest()
    return md5(str(data).encode("utf-8")).hexdigest()

# ---------------- DETECT CHANGE ----------------
def diff_significant(old_html, new_html, old_text, new_text, old_img_hash, new_img_hash):
    return old_html != new_html or old_text != new_text or old_img_hash != new_img_hash

# ---------------- SITE SELECTOR ----------------
def get_product_selector(url):
    """
    Returns default product container selector based on the domain.
    Add more sites here as needed.
    """
    domain = urlparse(url).netloc.lower()
    if "amazon." in domain:
        return "#dp-container"  # main product container
    elif "flipkart." in domain:
        return "div._1AtVbE"  # Flipkart product container
    # Add more e-commerce site selectors here
    else:
        return None  # fallback to viewport screenshot

# ---------------- MONITOR ----------------
def monitor_once():
    urls = [line.strip() for line in open("urls.txt") if line.strip()]
    old_status = load_status()
    new_status = {}

    for url in urls:
        print(f"Checking: {url}")
        selector = get_product_selector(url)
        html, text, screenshot = fetch_page(url, element_selector=selector)

        text_hash = md5_hash(text)
        html_hash = md5_hash(html)
        img_hash = md5_hash(screenshot)

        previous = old_status.get(url)
        new_status[url] = {"html_hash": html_hash, "text_hash": text_hash, "img_hash": img_hash}

        if not previous:
            print("First check — storing baseline.")
            continue

        if diff_significant(
            previous["html_hash"], html_hash,
            previous["text_hash"], text,
            previous["img_hash"], img_hash
        ):
            print("CHANGE DETECTED!")

            screenshot_path = "latest_snapshot.png"
            with open(screenshot_path, "wb") as f:
                f.write(screenshot)

            caption = f"🔔 Stock alert detected at: {url}"
            notify(caption, screenshot_path=screenshot_path)
        else:
            print("No meaningful change.")

    save_status(new_status)

# ---------------- LOOP ----------------
def loop_mode():
    while True:
        monitor_once()
        print(f"Sleeping {CHECK_INTERVAL_MIN} minutes...\n")
        time.sleep(CHECK_INTERVAL_MIN * 60)

# ---------------- MAIN ----------------
if __name__ == "__main__":
    # loop_mode()
    monitor_once()

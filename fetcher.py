from playwright.sync_api import sync_playwright

def fetch_page(url, element_selector=None):
    """
    Fetch a webpage and return:
    - html: full page HTML
    - text: visible page text
    - screenshot: bytes of cropped product section or default viewport
    
    Args:
        url (str): URL to fetch
        element_selector (str): CSS selector of product section (optional)
                                If None or selector not found, captures viewport.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        # Desktop viewport for proper rendering
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        )

        page = context.new_page()

        # Navigate and wait for main content
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=90000)
            page.wait_for_timeout(2500)  # allow JS to render

            html = page.content()
            text = page.inner_text("body")

            screenshot = None
            # If a selector is provided, try to screenshot that element
            if element_selector:
                try:
                    element = page.query_selector(element_selector)
                    if element:
                        screenshot = element.screenshot()
                except Exception as e:
                    print(f"Failed to capture element {element_selector}: {e}")

            # If element screenshot failed or not provided, take default viewport screenshot
            if screenshot is None:
                screenshot = page.screenshot(full_page=False)  # viewport only

        except Exception as e:
            print(f"Error fetching {url}: {e}")
            html, text, screenshot = "", "", b""

        finally:
            context.close()
            browser.close()

        return html, text, screenshot

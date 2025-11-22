from playwright.sync_api import Page, expect, sync_playwright
import time

def debug_streamlit_app(page: Page):
    page.goto("http://localhost:8501")
    time.sleep(3)
    page.screenshot(path="verification/debug_state.png")

    # Print all text content to see what's available
    print(page.content())

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            debug_streamlit_app(page)
        finally:
            browser.close()

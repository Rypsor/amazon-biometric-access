from playwright.sync_api import Page, expect, sync_playwright
import time

def verify_streamlit_app_final(page: Page):
    # 1. Arrange: Go to the Streamlit app.
    page.goto("http://localhost:8501")

    # 2. Assert: Check for the title and basic elements.
    expect(page.get_by_role("heading", name="Biometric Access Control")).to_be_visible(timeout=10000)

    # Just capture the main page state to verify the app is running and logic is loaded.
    time.sleep(2)
    page.screenshot(path="verification/streamlit_app_final.png")

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1280, 'height': 720})
        page = context.new_page()
        try:
            verify_streamlit_app_final(page)
        finally:
            browser.close()

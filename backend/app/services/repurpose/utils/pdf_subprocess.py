"""
PDF Generation Subprocess Worker.

This script is called as a subprocess to generate PDFs using Playwright.
On Windows, Playwright requires running on the main thread, which is not
possible from FastAPI's worker threads. This subprocess workaround ensures
Playwright runs on the main thread of its own process.

Usage (called internally by html_pdf_generator.py):
    python -m app.utils.pdf_subprocess

Input: HTML content via stdin (base64 encoded)
Output: PDF bytes via stdout (base64 encoded), or error message to stderr
"""

import sys
import base64
import json
import traceback


def generate_pdf_from_html(html_content: str) -> bytes:
    """
    Generate PDF from HTML using Playwright sync API.

    This function runs in the main thread of a subprocess,
    so Playwright works correctly on Windows.
    """
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )

        page = browser.new_page()
        page.set_content(html_content, wait_until='networkidle')
        page.wait_for_timeout(500)  # Wait for fonts

        pdf_bytes = page.pdf(
            format='Letter',
            print_background=True,
            margin={
                'top': '0',
                'right': '0',
                'bottom': '0',
                'left': '0'
            },
            prefer_css_page_size=True
        )

        browser.close()

    return pdf_bytes


def main():
    """
    Main entry point for subprocess.

    Protocol:
    1. Read JSON from stdin: {"html": "<base64 encoded HTML>"}
    2. Generate PDF
    3. Write JSON to stdout: {"success": true, "pdf": "<base64 encoded PDF>"}
       Or on error: {"success": false, "error": "<error message>"}
    """
    try:
        # Read input from stdin
        input_data = sys.stdin.read()
        request = json.loads(input_data)

        # Decode HTML from base64
        html_content = base64.b64decode(request['html']).decode('utf-8')

        # Generate PDF
        pdf_bytes = generate_pdf_from_html(html_content)

        # Encode PDF to base64 and output
        pdf_b64 = base64.b64encode(pdf_bytes).decode('ascii')

        response = {
            'success': True,
            'pdf': pdf_b64,
            'size': len(pdf_bytes)
        }

        print(json.dumps(response))
        sys.exit(0)

    except Exception as e:
        error_response = {
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }
        print(json.dumps(error_response))
        sys.exit(1)


if __name__ == '__main__':
    main()

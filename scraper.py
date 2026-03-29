import requests
from bs4 import BeautifulSoup


def fetch_page_content(url: str):
    """
    Fetches and cleans webpage content from the given URL.
    Tries requests first; if content seems JS-blocked, returns a warning.
    Returns (text_content, error_message).
    """
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

        session = requests.Session()
        response = session.get(url, headers=headers, timeout=20)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Remove non-content tags
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        clean_text = "\n".join(lines)

        # Detect JS-blocked pages
        js_block_phrases = [
            "javascript is not enabled",
            "please enable javascript",
            "you need to enable javascript",
            "this page requires javascript",
            "enable js",
        ]
        if any(phrase in clean_text.lower() for phrase in js_block_phrases) or len(clean_text) < 300:
            return None, "JS_BLOCKED"

        return clean_text[:8000], None

    except requests.exceptions.Timeout:
        return None, "Request timed out. The website took too long to respond."
    except requests.exceptions.ConnectionError:
        return None, "Could not connect to the URL. Check the link and try again."
    except requests.exceptions.HTTPError as e:
        return None, f"HTTP error {e.response.status_code}: The page returned an error."
    except Exception as e:
        return None, str(e)


def extract_text_from_html(html: str):
    """
    Extracts clean text from raw HTML pasted by the user.
    """
    try:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        clean_text = "\n".join(lines)
        return clean_text[:8000], None
    except Exception as e:
        return None, str(e)

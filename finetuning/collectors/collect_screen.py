import asyncio
import json
import os
from pathlib import Path
from playwright.async_api import async_playwright

# Curated diverse list of URLs
WEBSITES = [
    "https://google.com",
    "https://bing.com",
    "https://duckduckgo.com",
    "https://facebook.com",
    "https://twitter.com",
    "https://instagram.com",
    "https://linkedin.com",
    "https://youtube.com",
    "https://vimeo.com",
    "https://flickr.com",
    "https://amazon.com",
    "https://ebay.com",
    "https://walmart.com",
    "https://etsy.com",
    "https://bbc.com",
    "https://cnn.com",
    "https://theguardian.com",
    "https://nytimes.com",
    "https://reddit.com",
    "https://stackoverflow.com",
    "https://docs.google.com",
    "https://notion.so",
    "https://wikipedia.org",
    "https://mozilla.org",
    "https://github.com",
    "https://medium.com",
    "https://stackoverflow.com",
    "https://accounts.google.com",
    "https://login.live.com",
    "https://github.com/login"
]

OUTPUT_JSONL = "dataset/dom_screenshots.jsonl"
SCREENSHOT_DIR = "dataset/screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# JS to extract basic info + approximate CSS selector
JS_EXTRACT_ELEMENTS = """
() => {
    const elements = Array.from(document.querySelectorAll('*'));

    function genSelector(el) {
        if (el.id) return `${el.tagName.toLowerCase()}#${el.id}`;
        if (el.className && typeof el.className === 'string')
            return `${el.tagName.toLowerCase()}.${el.className.trim().split(/\\s+/).join('.')}`;
        return el.tagName.toLowerCase();
    }

    return elements.map(el => ({
        selector: genSelector(el),
        tag: el.tagName.toLowerCase(),
        text: el.textContent.trim(),
        type: el.getAttribute('type') || "",
        value: el.value || ""
    }));
};
"""

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        for url in WEBSITES:
            try:
                context = await browser.new_context()
                page = await context.new_page()

                print(f"[VISIT] {url}")
                await page.goto(url, timeout=30000)
                await page.wait_for_load_state("networkidle")

                # Screenshot
                name_safe = url.replace("https://", "").replace("http://", "").replace("/", "_")
                screenshot_path = f"{SCREENSHOT_DIR}/{name_safe}.png"
                await page.screenshot(path=screenshot_path, full_page=True)

                # Extract DOM+metadata
                raw_data = await page.evaluate(JS_EXTRACT_ELEMENTS)
                enriched = []
                for elem in raw_data:
                    try:
                        handle = await page.query_selector(elem["selector"])
                        if not handle:
                            continue
                        box = await handle.bounding_box()
                        if not box:
                            continue
                        enriched.append({
                            "tag": elem["tag"],
                            "selector": elem["selector"],
                            "text": elem["text"],
                            "type": elem["type"],
                            "value": elem["value"],
                            "box": {
                                "x": box["x"],
                                "y": box["y"],
                                "w": box["width"],
                                "h": box["height"]
                            }
                        })
                    except Exception:
                        pass

                entry = {
                    "url": url,
                    "screenshot": screenshot_path,
                    "elements": enriched
                }
                with open(OUTPUT_JSONL, "a", encoding="utf-8") as f:
                    f.write(json.dumps(entry) + "\n")

                await context.close()

            except Exception as e:
                print(f"[ERROR] {url}: {e}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
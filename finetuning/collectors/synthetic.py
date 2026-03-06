import os
import json
import random
from faker import Faker
from pathlib import Path
import asyncio
from playwright.async_api import async_playwright
import uuid
fake = Faker()

# Directories
OUTPUT_DIR = Path("synthetic_pages")
SCREENSHOT_DIR = OUTPUT_DIR / "screenshots"
JSONL_FILE = OUTPUT_DIR / "synthetic_dataset.jsonl"
OUTPUT_DIR.mkdir(exist_ok=True)
SCREENSHOT_DIR.mkdir(exist_ok=True)

# Page settings
NUM_PAGES = 100  # adjust for larger datasets
PAGE_WIDTH = 1200
PAGE_HEIGHT = 800
ELEMENT_TYPES = ['button', 'a', 'input_text', 'textarea', 'select']

def random_box():
    """Generate a random bounding box within the page."""
    w = random.randint(60, 200)
    h = random.randint(20, 60)
    x = random.randint(0, PAGE_WIDTH - w)
    y = random.randint(0, PAGE_HEIGHT - h)
    return {"x": x, "y": y, "w": w, "h": h}

def generate_element():
    elem_type = random.choice(ELEMENT_TYPES)
    box = random_box()
    element = {"box": box}

    uid = uuid.uuid4().hex[:6]  # unique short id

    if elem_type == "button":
        element.update({
            "tag": "button",
            "text": fake.word().capitalize(),
            "selector": f"button#{uid}",
            "type": "",
            "value": ""
        })
    elif elem_type == "a":
        element.update({
            "tag": "a",
            "text": fake.word().capitalize(),
            "selector": f"a#{uid}",
            "href": fake.url(),
            "type": "",
            "value": ""
        })
    elif elem_type == "input_text":
        element.update({
            "tag": "input",
            "text": "",
            "selector": f"input#{uid}",
            "type": "text",
            "value": fake.word()
        })
    elif elem_type == "textarea":
        element.update({
            "tag": "textarea",
            "text": fake.sentence(),
            "selector": f"textarea#{uid}",
            "type": "",
            "value": fake.sentence()
        })
    elif elem_type == "select":
        options = [fake.word() for _ in range(random.randint(2, 5))]
        element.update({
            "tag": "select",
            "text": "",
            "selector": f"select#{uid}",
            "type": "",
            "value": options[0],
            "options": options
        })
    return element

def generate_html_page(elements, page_index):
    """Create HTML page with inline CSS positioning."""
    html_elements = []
    for elem in elements:
        style = f"position:absolute; left:{elem['box']['x']}px; top:{elem['box']['y']}px; width:{elem['box']['w']}px; height:{elem['box']['h']}px;"
        if elem['tag'] == "button":
            html_elements.append(f"<button id='{elem['selector'].split('#')[1]}' style='{style}'>{elem['text']}</button>")
        elif elem['tag'] == "a":
            html_elements.append(f"<a id='{elem['selector'].split('#')[1]}' href='{elem['href']}' style='{style}'>{elem['text']}</a>")
        elif elem['tag'] == "input":
            html_elements.append(f"<input id='{elem['selector'].split('#')[1]}' type='text' value='{elem['value']}' style='{style}'>")
        elif elem['tag'] == "textarea":
            html_elements.append(f"<textarea id='{elem['selector'].split('#')[1]}' style='{style}'>{elem['text']}</textarea>")
        elif elem['tag'] == "select":
            options_html = "".join([f"<option>{opt}</option>" for opt in elem['options']])
            html_elements.append(f"<select id='{elem['selector'].split('#')[1]}' style='{style}'>{options_html}</select>")

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Synthetic Page {page_index}</title>
        <meta charset="UTF-8">
    </head>
    <body style="position:relative; width:{PAGE_WIDTH}px; height:{PAGE_HEIGHT}px; margin:0; padding:0;">
        {''.join(html_elements)}
    </body>
    </html>
    """
    return html_content

# JS snippet to extract interactive elements in Playwright
JS_INTERACTIVE_ELEMENTS = """
() => {
    const elements = Array.from(document.querySelectorAll('*'));
    function genSelector(el) {
        if (el.id) return `${el.tagName.toLowerCase()}#${el.id}`;
        if (el.className && typeof el.className === 'string')
            return `${el.tagName.toLowerCase()}.${el.className.trim().split(/\\s+/).join('.')}`;
        return el.tagName.toLowerCase();
    }
    return elements
        .filter(el => {
            const tag = el.tagName.toLowerCase();
            const type = el.getAttribute('type') || "";
            const role = el.getAttribute('role') || "";
            return (
                tag === 'button' ||
                (tag === 'a' && el.hasAttribute('href')) ||
                tag === 'textarea' ||
                tag === 'select' ||
                (tag === 'input' && ['text','password','email','number','tel','checkbox','radio','submit','date','url','search','color','range'].includes(type)) ||
                ['button','link','menuitem','tab','option'].includes(role)
            );
        })
        .map(el => ({
            selector: genSelector(el),
            tag: el.tagName.toLowerCase(),
            text: el.textContent.trim(),
            type: el.getAttribute('type') || "",
            value: el.value || ""
        }));
};
"""

async def generate_dataset():
    entries = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        for i in range(NUM_PAGES):
            elements = [generate_element() for _ in range(random.randint(5, 15))]
            html_content = generate_html_page(elements, i)
            html_file = OUTPUT_DIR / f"page_{i}.html"
            html_file.write_text(html_content, encoding="utf-8")

            context = await browser.new_context(viewport={"width": PAGE_WIDTH, "height": PAGE_HEIGHT})
            page = await context.new_page()
            await page.goto(f"file://{html_file.resolve()}")
            await page.wait_for_load_state("networkidle")

            # Screenshot
            screenshot_path = SCREENSHOT_DIR / f"page_{i}.png"
            await page.screenshot(path=str(screenshot_path), full_page=True)

            # Extract DOM
            raw_elements = await page.evaluate(JS_INTERACTIVE_ELEMENTS)
            enriched = []
            for elem in raw_elements:
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
                except:
                    continue

            # Save JSONL entry
            entry = {
                "page": str(html_file),
                "screenshot": str(screenshot_path),
                "elements": enriched
            }
            entries.append(entry)
            await context.close()
            print(f"[DONE] Page {i} processed with {len(enriched)} interactive elements.")

        # Save JSONL
        with open(JSONL_FILE, "w", encoding="utf-8") as f:
            for e in entries:
                f.write(json.dumps(e) + "\n")

        await browser.close()
        print(f"[FINISHED] Synthetic dataset saved: {JSONL_FILE}")

if __name__ == "__main__":
    asyncio.run(generate_dataset())
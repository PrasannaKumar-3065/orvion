import asyncio
import json
import os
import time
from playwright.async_api import async_playwright

# --- CONFIG ---
SAVE_DIR = "manual_dataset"
os.makedirs(SAVE_DIR, exist_ok=True)

async def run_recorder():
    print(f"📸 Manual Recorder (High Fidelity) Started")
    print(f"📂 Saving to: ./{SAVE_DIR}")
    print("-" * 40)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={"width": 1280, "height": 720})
        page = await context.new_page()

        await page.goto(
            "https://parabank.parasoft.com/parabank/index.htm",
            wait_until="domcontentloaded",
            timeout=60000
        )

        step_count = 1
        
        while True:
            user_input = input(f"\n[Step {step_count}] Press ENTER to capture (or 'q' to quit): ")
            if user_input.lower() == 'q':
                break

            timestamp = int(time.time())
            img_filename = f"step_{step_count}_{timestamp}.png"
            img_path = os.path.join(SAVE_DIR, img_filename)
            await page.screenshot(path=img_path)

            # --- IMPROVED DOM SCRAPER ---
            # Now hunts for data-test, aria-label, placeholder, and classes
            dom_data = await page.evaluate("""
                Array.from(document.querySelectorAll('input, button, a, select, textarea, [role="button"]'))
                .map(el => {
                    let sel = '';
                    
                    // Priority 1: ID (Best)
                    if (el.id) {
                        sel = '#' + el.id;
                    } 
                    // Priority 2: Name
                    else if (el.name) {
                        sel = `[name="${el.name}"]`;
                    } 
                    // Priority 3: Data Attributes (Common in Testing)
                    else if (el.getAttribute('data-test')) {
                        sel = `[data-test="${el.getAttribute('data-test')}"]`;
                    }
                    else if (el.getAttribute('data-testid')) {
                        sel = `[data-testid="${el.getAttribute('data-testid')}"]`;
                    }
                    // Priority 4: Accessibility Labels
                    else if (el.getAttribute('aria-label')) {
                        sel = `[aria-label="${el.getAttribute('aria-label')}"]`;
                    }
                    // Priority 5: Placeholder (Good for inputs)
                    else if (el.getAttribute('placeholder')) {
                        sel = `[placeholder="${el.getAttribute('placeholder')}"]`;
                    }
                    // Priority 6: Class (Last resort, cleaned up)
                    else if (el.className && typeof el.className === 'string') {
                        // Take the first distinct class that looks useful
                        const classes = el.className.split(' ').filter(c => c.trim().length > 0);
                        if (classes.length > 0) {
                            sel = '.' + classes.join('.');
                        }
                    }

                    // If we still have no selector, skip it (can't automate it easily)
                    if (!sel) return null;

                    return {
                        tag: el.tagName.toLowerCase(),
                        selector: sel,
                        text: el.innerText.slice(0, 50).replace(/\\n/g, ' ').trim() || '',
                        type: el.type || '',
                        value: el.value || ''
                    };
                }).filter(e => e !== null)
            """)
            
            dom_filename = f"step_{step_count}_{timestamp}_dom.txt"
            dom_path = os.path.join(SAVE_DIR, dom_filename)
            
            with open(dom_path, "w", encoding="utf-8") as f:
                f.write(json.dumps(dom_data, indent=2))

            print(f"✅ Captured {len(dom_data)} elements!")
            print(f"   Image: {img_filename}")
            print(f"   DOM:   {dom_filename}")
            
            step_count += 1

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_recorder())
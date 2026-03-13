import asyncio
from playwright.async_api import async_playwright
import os
import random

OUTPUT_DIR = "ui_screenshots"
os.makedirs(OUTPUT_DIR, exist_ok=True)

URLS = [
    "https://www.wikipedia.org",
    "https://en.wikipedia.org/wiki/Artificial_intelligence",
    "https://github.com",
    "https://stackoverflow.com",
    "https://www.reddit.com",
    "https://news.ycombinator.com",
    "https://www.nytimes.com",
    "https://www.bbc.com",
    "https://www.amazon.com",
    "https://www.ebay.com",
    "https://www.linkedin.com",
    "https://twitter.com",
    "https://medium.com",
    "https://www.nationalgeographic.com",
    "https://www.airbnb.com",
    "https://www.booking.com",
    "https://www.cnn.com",
    "https://www.apple.com",
    "https://www.microsoft.com",
    "https://www.netflix.com",
    "https://www.tesla.com",
    "https://www.kaggle.com",
    "https://www.npmjs.com",
    "https://pypi.org",
    "https://developer.mozilla.org",
    "https://openai.com",
    "https://huggingface.co",
    "https://arxiv.org",
    "https://duckduckgo.com",
    "https://yahoo.com",
    "https://imdb.com",
    "https://producthunt.com",
    "https://dribbble.com",
    "https://behance.net",
    "https://figma.com",
    "https://slack.com",
    "https://notion.so",
    "https://trello.com",
    "https://asana.com",
    "https://stripe.com",
    "https://digitalocean.com",
    "https://cloudflare.com",
    "https://vercel.com",
    "https://supabase.com",
    "https://tailwindcss.com",
    "https://react.dev",
    "https://vuejs.org",
    "https://angular.io",
    "https://getbootstrap.com",
    "https://chakra-ui.com",
    "https://mui.com",
]

async def screenshot_page(page, url, index):
    try:
        await page.goto(url, timeout=60000)
        await page.wait_for_timeout(3000)

        filename = f"{OUTPUT_DIR}/site_{index}.png"

        await page.screenshot(
            path=filename,
            full_page=True
        )

        print(f"Saved {filename}")

    except Exception as e:
        print(f"Failed {url}: {e}")

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)

        context = await browser.new_context(
            viewport={"width":1280,"height":800}
        )

        page = await context.new_page()

        index = 0

        for url in URLS:
            await screenshot_page(page, url, index)
            index += 1

            # extra random screenshots to reach ~100
            if random.random() > 0.5:
                try:
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await page.wait_for_timeout(2000)

                    filename = f"{OUTPUT_DIR}/site_{index}.png"
                    await page.screenshot(path=filename, full_page=False)

                    print(f"Saved {filename}")
                    index += 1

                except:
                    pass

        await browser.close()

asyncio.run(main())
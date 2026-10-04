import asyncio
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from playwright.async_api import async_playwright

async def inspect_img_alt():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            locale="vi-VN",
            viewport={"width": 1280, "height": 800},
        )
        page = await context.new_page()
        await page.goto("https://www.tiktok.com/explore", wait_until="networkidle", timeout=30000)
        
        cards = await page.evaluate("""() => {
            return Array.from(document.querySelectorAll('img')).map(img => ({
                alt: img.alt,
                src: img.src,
                parentA: img.closest('a') ? img.closest('a').href : ''
            })).filter(x => x.parentA.includes('/video/'));
        }""")
        
        print(f"Images with video links ({len(cards)}):")
        for c in cards[:5]:
            print(" -> Video Link:", c['parentA'])
            print(" -> Alt text:", c['alt'])
            print(" -> Image Src:", c['src'][:50])
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(inspect_img_alt())

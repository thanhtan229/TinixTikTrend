"""User-operated sign-in helper. Run explicitly; no automated credential/CAPTCHA actions."""
import asyncio
import argparse
from playwright.async_api import async_playwright
from app.collectors.tiktok_shop.session import load_state, save_state, SessionStateError


async def main():
    try:
        state = load_state()
    except SessionStateError:
        state = None  # Explicit reconnect can replace a corrupted state.
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)
        try:
            context = await browser.new_context(locale='vi-VN', storage_state=state)
            page = await context.new_page()
            await page.goto('https://www.tiktok.com/login', wait_until='domcontentloaded')
            print('Tu dang nhap TikTok trong cua so vua mo. Khong gui mat khau/OTP cho agent.')
            print('Neu TikTok yeu cau xac minh, hay tu thuc hien. Script khong tu vuot Security Check.')
            answer = await asyncio.to_thread(input, 'Sau khi xong, nhap SAVE de luu phien cuc bo; Enter de huy: ')
            if answer.strip().upper() == 'SAVE':
                save_state(await context.storage_state())
                print('Da luu phien cuc bo. Quay lai dashboard va thu quet; viec luu khong dam bao TikTok cho phep truy cap Shop.')
            else:
                print('Da huy; phien cu duoc giu nguyen.')
        finally:
            await browser.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='User-operated local TikTok session setup')
    parser.add_argument('--check', action='store_true', help='Validate saved state without opening a browser')
    args = parser.parse_args()
    if args.check:
        try:
            state = load_state()
            usable = bool(state and (state['cookies'] or state['origins']))
            print('LOCAL_SESSION_AVAILABLE' if usable else 'NO_LOCAL_SESSION')
            print('Session availability is not proof of successful TikTok Shop access.')
        except SessionStateError:
            print('INVALID_LOCAL_SESSION: run CONNECT_TIKTOK.bat to reconnect.')
            raise SystemExit(1)
    else:
        asyncio.run(main())

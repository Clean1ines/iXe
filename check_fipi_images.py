import asyncio
from playwright.async_api import async_playwright
import tempfile
import os
import re

async def check_image_presence():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto('https://ege.fipi.ru/bank/questions.php?proj=AC437B34557F88EA4115D2F374B0A07B&page=init', wait_until='networkidle')
        await page.wait_for_timeout(5000)
        content = await page.content()
        
        if '<img' in content.lower():
            print('FOUND: <img> tags in the rendered HTML')
            img_srcs = re.findall(r'<img[^>]*src=[\""]([^\""]*)[\""]', content, re.IGNORECASE)
            print(f'Image sources found: {img_srcs}')
        else:
            print('NOT FOUND: No <img> tags in the rendered HTML')
        
        if 'showpicture' in content.lower():
            print('FOUND: ShowPicture scripts in the rendered HTML')
        else:
            print('NOT FOUND: No ShowPicture scripts in the rendered HTML')
            
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write(content)
            print(f'HTML content saved to: {f.name}')
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(check_image_presence())

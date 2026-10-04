import asyncio
import sys
import json

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

from playwright.async_api import async_playwright
from app.collectors.tiktok_shop.parser import extract_product_from_html

async def test_product_scrape():
    # Test sample HTML with TikTok Shop Vietnam structure
    sample_shop_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Son Kem Lì Mịn Môi Kháng Nước Velvet Lip Tint 5g - TikTok Shop VN</title>
        <script type="application/ld+json">
        {
            "@context": "https://schema.org",
            "@type": "Product",
            "name": "Son Kem Lì Mịn Môi Kháng Nước Velvet Lip Tint 5g",
            "productID": "17293849102",
            "image": ["https://p16-va.lemon8cdn.com/tos-alisg-v-a3e472/oIDefA9.jpg"],
            "category": "Sức khỏe & Làm đẹp",
            "brand": {"@type": "Brand", "name": "Cosmetics Official Store VN"},
            "offers": {
                "@type": "Offer",
                "price": "149000",
                "priceCurrency": "VND"
            },
            "aggregateRating": {
                "@type": "AggregateRating",
                "ratingValue": "4.9",
                "reviewCount": "195"
            }
        }
        </script>
    </head>
    <body>
        <h1>Son Kem Lì Mịn Môi Kháng Nước Velvet Lip Tint 5g</h1>
    </body>
    </html>
    """
    
    prod = extract_product_from_html(sample_shop_html, page_url="https://shop.tiktok.com/view/product/17293849102")
    print("Extracted Product Result:")
    print(" -> ID:", prod.external_product_id)
    print(" -> Title:", prod.title)
    print(" -> Price:", prod.price)
    print(" -> Rating:", prod.rating)
    print(" -> Reviews:", prod.review_count)
    print(" -> Shop:", prod.shop_name)
    print(" -> Category:", prod.category)

if __name__ == "__main__":
    asyncio.run(test_product_scrape())

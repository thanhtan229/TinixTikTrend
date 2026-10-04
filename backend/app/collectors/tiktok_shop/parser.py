import re
import json
import html as html_utils
import math
from typing import List, Optional, Dict, Any
from urllib.parse import urljoin
from app.collectors.tiktok_shop.schemas import ExtractedProduct
from app.core.urls import validate_product_url, product_id_from_url


def is_security_check(html: str) -> bool:
    return bool(re.search(r'<title[^>]*>\s*(?:Security Check|Access Denied)\s*</title>', html or '', re.I))


def parse_numeric_string(raw: Optional[str]) -> Optional[int]:
    if raw is None or isinstance(raw, bool) or str(raw).strip().startswith('-'):
        return None
    match = re.search(r'(\d[\d.,]*)\s*(k|m|nghìn|triệu)?', str(raw).strip().lower())
    if not match:
        return None
    number, suffix = match.groups()
    if suffix:
        # A suffix uses a decimal separator; grouped counts have no suffix.
        if ',' in number and '.' in number:
            return None
        number = number.replace(',', '.')
        if number.count('.') > 1:
            return None
        factor = 1_000_000 if suffix in ('m', 'triệu') else 1_000
    else:
        if re.fullmatch(r'\d{1,3}(?:[.,]\d{3})+', number):
            number = number.replace('.', '').replace(',', '')
        elif re.fullmatch(r'\d+', number) is None:
            return None
        factor = 1
    try:
        return int(float(number) * factor)
    except (ValueError, OverflowError):
        return None


def parse_price_string(raw: Optional[str]) -> Optional[float]:
    if raw is None:
        return None
    cleaned = re.sub(r'[^\d.,]', '', str(raw))
    if not cleaned:
        return None
    if re.fullmatch(r'\d{1,3}(?:[.,]\d{3})+', cleaned):
        cleaned = cleaned.replace('.', '').replace(',', '')
    elif ',' in cleaned and '.' in cleaned:
        decimal = max(cleaned.rfind(','), cleaned.rfind('.'))
        cleaned = re.sub(r'[.,]', '', cleaned[:decimal]) + '.' + cleaned[decimal+1:]
    else:
        cleaned = cleaned.replace(',', '.')
    try:
        value = float(cleaned)
        return value if math.isfinite(value) and not str(raw).strip().startswith('-') else None
    except ValueError:
        return None


def extract_script_tag_content(html: str, tag_id: str) -> Optional[str]:
    found = re.search(rf'<script[^>]*id=["\']{re.escape(tag_id)}["\'][^>]*>(.*?)</script>', html, re.S | re.I)
    return found.group(1).strip() if found else None


def extract_json_ld(html: str) -> List[Dict[str, Any]]:
    results = []
    for content in re.findall(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html, re.S | re.I):
        try:
            data = json.loads(content)
            items = data if isinstance(data, list) else [data]
            for item in items:
                if isinstance(item, dict):
                    results.extend(item.get('@graph', [item]))
        except (ValueError, TypeError):
            continue
    return [x for x in results if isinstance(x, dict)]


def extract_product_from_json_ld(items: List[Dict[str, Any]], page_url: Optional[str] = None) -> Optional[ExtractedProduct]:
    for item in items:
        if item.get('@type') != 'Product':
            continue
        try:
            url = validate_product_url(page_url or item.get('url') or '')
            ext_id = product_id_from_url(url)
            # Recommendations may contain several Products. Never assign a sibling's
            # metadata to the requested identity, even if productID is absent.
            for declared_url in (item.get('url'), item.get('@id')):
                if isinstance(declared_url, str) and declared_url.startswith('https://'):
                    if product_id_from_url(declared_url.split('#')[0]) != ext_id:
                        raise ValueError('JSON-LD identity does not match the requested product.')
            declared_id = item.get('productID')
            if declared_id is not None and str(declared_id) != ext_id:
                continue
            title = item.get('name')
            if not isinstance(title, str) or not title.strip():
                continue
            offers = item.get('offers') or {}
            if isinstance(offers, list):
                offers = offers[0] if offers else {}
            rating = item.get('aggregateRating') or {}
            seller = offers.get('seller') or item.get('brand') or {}
            image = item.get('image')
            if isinstance(image, list):
                image = image[0] if image else None
            currency = offers.get('priceCurrency')
            offer_url = offers.get('url')
            if isinstance(offer_url, str) and offer_url.startswith('https://'):
                if product_id_from_url(offer_url) != ext_id:
                    continue
            return ExtractedProduct(external_product_id=ext_id, title=title.strip(), url=url,
                image_url=image if isinstance(image, str) else None,
                shop_name=seller.get('name') if isinstance(seller, dict) else None,
                category=item.get('category') if isinstance(item.get('category'), str) else None,
                price=parse_price_string(str(offers['price'])) if offers.get('price') is not None and currency == 'VND' else None,
                rating=float(rating['ratingValue']) if rating.get('ratingValue') is not None else None,
                review_count=parse_numeric_string(str(rating['reviewCount'])) if rating.get('reviewCount') is not None else None)
        except (ValueError, TypeError, AttributeError):
            continue
    return None


def extract_product_from_modern_router(html: str, page_url: Optional[str]) -> Optional[ExtractedProduct]:
    """Read the VN PDP product component, never sibling cards or shop totals."""
    embedded = extract_script_tag_content(html, '__MODERN_ROUTER_DATA__')
    if not embedded:
        return None
    try:
        url = validate_product_url(page_url or '')
        requested_id = product_id_from_url(url)
        routes = json.loads(embedded).get('loaderData', {})
        if not isinstance(routes, dict):
            return None
        for page in routes.values():
            if not isinstance(page, dict):
                continue
            config = page.get('page_config') or {}
            if config.get('global_fe_config', {}).get('page_name') != 'product_detail':
                continue
            if page.get('region_info', {}).get('sale_region') != 'VN':
                continue
            for component in config.get('components_map', []):
                if not isinstance(component, dict) or component.get('component_name') != 'product_info':
                    continue
                data = component.get('component_data') or {}
                if data.get('error_code') != 0:
                    continue
                product = data.get('product_info') or {}
                title = product.get('title')
                if str(product.get('product_id')) != requested_id or not isinstance(title, str) or not title.strip():
                    continue
                price = product.get('price') or {}
                review = product.get('review') or {}
                seller = product.get('seller') or {}
                images = product.get('images') or []
                image_urls = images[0].get('url_list', []) if images and isinstance(images[0], dict) else []
                categories = data.get('categories') or []
                category = next((c.get('category_name') for c in categories
                    if isinstance(c, dict) and c.get('level') == 1 and isinstance(c.get('category_name'), str)), None)
                try:
                    rating = float(review['product_rating'])
                    if not math.isfinite(rating) or not 0 <= rating <= 5:
                        rating = None
                except (KeyError, ValueError, TypeError):
                    rating = None
                # real_price is the formatted display price (minimum for a SKU range).
                # Only explicitly VND prices are usable by the local price filters.
                return ExtractedProduct(external_product_id=requested_id, title=title.strip(), url=url,
                    image_url=image_urls[0] if image_urls and isinstance(image_urls[0], str) else None,
                    shop_id=str(product['seller_id']) if product.get('seller_id') is not None else None,
                    shop_name=seller.get('name') if isinstance(seller.get('name'), str) else None,
                    category=category,
                    price=parse_price_string(price.get('real_price')) if price.get('currency') == 'VND' else None,
                    original_price=parse_price_string(price.get('original_price')) if price.get('currency') == 'VND' else None,
                    sold_count=parse_numeric_string(product.get('sold_count')),
                    review_count=parse_numeric_string(review.get('review_count')), rating=rating)
    except (ValueError, TypeError, AttributeError, IndexError):
        return None
    return None


def extract_product_from_html(html: str, page_url: Optional[str] = None) -> Optional[ExtractedProduct]:
    if not html:
        return None
    modern = extract_product_from_modern_router(html, page_url)
    if modern:
        return modern
    json_ld = extract_product_from_json_ld(extract_json_ld(html), page_url)
    # Only documented, structured product identity is accepted; title-only/error pages are not products.
    embedded = extract_script_tag_content(html, '__UNIVERSAL_DATA_FOR_REHYDRATION__')
    if embedded:
        try:
            scope = json.loads(embedded).get('__DEFAULT_SCOPE__', {})
            for key, val in scope.items():
                if not isinstance(val, dict) or not ('product' in key.lower() or 'shop' in key.lower()):
                    continue
                ext_id = str(val.get('product_id', ''))
                title = val.get('title') or val.get('product_name')
                url = validate_product_url(page_url or '')
                if ext_id != product_id_from_url(url) or not isinstance(title, str) or not title.strip():
                    continue
                product = json_ld or ExtractedProduct(external_product_id=ext_id, title=title.strip(), url=url)
                sold = val.get('sold_count', val.get('sales_count'))
                product.sold_count = parse_numeric_string(str(sold)) if sold is not None else None
                # real_price units have not been verified for VN: retain unknown price as null.
                return product
        except (ValueError, TypeError, AttributeError):
            pass
    return json_ld


def extract_product_urls_from_listing_html(html: str, base_url: str = 'https://www.tiktok.com') -> List[str]:
    # JSON hydration frequently escapes slashes; HTML attributes escape ampersands.
    html = html_utils.unescape(html or '').replace('\\/', '/').replace('\\u002F', '/').replace('\\u002f', '/')
    # Match the entire URL before validating: never truncate /123/extra into /123.
    candidates = re.findall(r'https://(?:[a-zA-Z0-9-]+\.)?tiktok\.com/[^\s"\'<>\\]+', html or '')
    for href in re.findall(r'href=["\']([^"\']+)["\']', html or ''):
        candidates.append(urljoin(base_url, href))
    result = []
    for candidate in candidates:
        try:
            result.append(validate_product_url(candidate))
        except ValueError:
            continue
    return list(dict.fromkeys(result))

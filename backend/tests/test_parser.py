import os
import json
import pytest
from app.collectors.tiktok_shop.parser import (
    parse_numeric_string,
    parse_price_string,
    extract_product_from_html,
    extract_product_urls_from_listing_html,
)
from app.collectors.tiktok_shop.schemas import ExtractedProduct

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def test_parse_numeric_strings():
    assert parse_numeric_string("1.2k") == 1200
    assert parse_numeric_string("2.5M") == 2500000
    assert parse_numeric_string("12,500 sold") == 12500
    assert parse_numeric_string("500") == 500
    assert parse_numeric_string(None) is None
    assert parse_numeric_string("invalid") is None


def test_parse_price_strings():
    assert parse_price_string("149.000₫") == 149000.0
    assert parse_price_string("149,000 VND") == 149000.0
    assert parse_price_string("19.99") == 19.99
    assert parse_price_string(None) is None


def test_extract_product_from_html_fixture():
    fixture_path = os.path.join(FIXTURES_DIR, "product_page.html")
    with open(fixture_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    product = extract_product_from_html(
        html_content,
        page_url="https://shop.tiktok.com/view/product/17293849102"
    )

    assert product is not None
    assert isinstance(product, ExtractedProduct)
    assert product.external_product_id == "17293849102"
    assert product.title == "Son Kem Lì Mịn Môi Velvet Lip Tint 5g"
    assert product.price == 149000.0
    assert product.rating == 4.9
    assert product.review_count == 195
    assert product.shop_name == "Cosmetics Official Store VN"
    assert product.category == "Sức khỏe & Làm đẹp"


def test_extract_product_urls_from_listing_html():
    sample_listing = """
    <div>
        <a href="/view/product/17293849102">Product 1</a>
        <a href="https://shop.tiktok.com/view/product/17293849103">Product 2</a>
        <a href="/tag/trending">Tag Link</a>
        <a href="/@seller/video/123456">Video Link</a>
    </div>
    """
    urls = extract_product_urls_from_listing_html(sample_listing)
    assert len(urls) == 2
    assert "https://www.tiktok.com/view/product/17293849102" in urls
    assert "https://shop.tiktok.com/view/product/17293849103" in urls


def test_listing_parser_rejects_truncated_and_resolves_relative_product_paths():
    html = '''<a href="/vn/pdp/123456">valid</a>
      <a href="https://shop.tiktok.com/vn/pdp/987654/extra">invalid</a>'''
    assert extract_product_urls_from_listing_html(html, 'https://shop.tiktok.com/vn/c/food') == [
        'https://shop.tiktok.com/vn/pdp/123456']


@pytest.mark.parametrize('field', ['url', '@id', 'offer'])
def test_recommended_product_cannot_supply_requested_metadata(field):
    requested = 'https://shop.tiktok.com/view/product/123456'
    sibling = {'@type': 'Product', 'name': 'Other product'}
    wrong_url = 'https://shop.tiktok.com/view/product/987654'
    if field == 'offer':
        sibling['offers'] = {'url': wrong_url, 'price': 100, 'priceCurrency': 'VND'}
    else:
        sibling[field] = wrong_url
    content = '<script type="application/ld+json">' + json.dumps(sibling) + '</script>'
    assert extract_product_from_html(content, requested) is None
    correct = {'@type': 'Product', 'name': 'Requested product', 'url': requested}
    content = '<script type="application/ld+json">' + json.dumps([sibling, correct]) + '</script>'
    assert extract_product_from_html(content, requested).title == 'Requested product'


def test_escaped_hydration_links_are_discovered_without_video_fallback():
    html = r'''<script>{"url":"https:\/\/shop.tiktok.com\/view\/product\/123456"}</script>
    <script>{"url":"https:\u002f\u002fwww.tiktok.com\u002fproduct\u002f987654"}</script>
    <a href="https://shop.tiktok.com/view/product/123456?x=1&amp;y=2">Same</a>
    <a href="https://www.tiktok.com/@creator/video/999999">Video</a>'''
    assert extract_product_urls_from_listing_html(html) == [
        'https://shop.tiktok.com/view/product/123456', 'https://www.tiktok.com/product/987654']


def test_invalid_negative_metrics_are_not_converted_to_positive():
    assert parse_numeric_string('-12 sold') is None
    assert parse_numeric_string(True) is None
    assert parse_price_string('-149.000₫') is None
    assert parse_price_string('9' * 400) is None


def test_vn_pdp_tracking_link_validation_and_identity():
    from app.core.urls import validate_product_url, product_id_from_url
    from app.api.crawler import CrawlRequest
    url = 'https://shop.tiktok.com/vn/pdp/1737036472084039604'
    tracking = url + '?source=ecommerce_category&btm_transfer_id=fixture#detail'
    assert validate_product_url(tracking) == url
    assert product_id_from_url(tracking) == '1737036472084039604'
    assert CrawlRequest(product_urls=[tracking]).product_urls == [url]
    assert extract_product_urls_from_listing_html(json.dumps({'link': tracking})) == [url]
    ld = {'@type': 'Product', 'name': 'PDP fixture', 'url': tracking,
          'offers': {'priceCurrency': 'VND', 'price': 100000}}
    html = '<script type="application/ld+json">' + json.dumps(ld) + '</script>'
    assert extract_product_from_html(html, url).price == 100000
    ld['url'] = 'https://shop.tiktok.com/vn/pdp/999999'
    assert extract_product_from_html('<script type="application/ld+json">' + json.dumps(ld) + '</script>', url) is None


@pytest.mark.parametrize('path', ['/vn/pdp/abc', '/vn/pdp/123/extra', '/vn/pdp/123.evil',
    '/vn/pdp/%31%32%33', '/us/pdp/123', '/vn/pdp/../123'])
def test_vn_pdp_does_not_expand_to_arbitrary_paths(path):
    from app.core.urls import validate_product_url
    with pytest.raises(ValueError):
        validate_product_url('https://shop.tiktok.com' + path)


@pytest.fixture
def vn_router():
    # Selected public fields observed on a real VN PDP; no session/reviewer data.
    with open(os.path.join(FIXTURES_DIR, 'vn_pdp_router.json'), encoding='utf-8') as f:
        return json.load(f)


def parse_vn_router(data):
    return extract_product_from_html('<script id="__MODERN_ROUTER_DATA__">' +
        json.dumps(data) + '</script>', 'https://shop.tiktok.com/vn/pdp/1737036472084039604')


def router_component(data):
    return next(iter(data['loaderData'].values()))['page_config']['components_map'][0]


def test_vn_pdp_uses_product_metrics_instead_of_shop_totals(vn_router):
    product = parse_vn_router(vn_router)
    assert product.external_product_id == '1737036472084039604'
    assert product.price == 43965
    assert product.original_price == 54956
    assert product.sold_count == 12808
    assert product.review_count == 730
    assert product.rating == 4.6
    assert product.shop_name == 'BĂNG BĂNG FOOD'
    assert product.shop_id == '7494829868722129844'
    assert product.category == 'Đồ ăn & Đồ uống'
    assert product.image_url == 'https://example.com/product.webp'


def test_vn_pdp_missing_metrics_are_null_and_zero_is_preserved(vn_router):
    data = router_component(vn_router)['component_data']['product_info']
    data.pop('price')
    data.pop('review')
    data['sold_count'] = '0'
    product = parse_vn_router(vn_router)
    assert product.sold_count == 0
    assert product.price is None and product.original_price is None
    assert product.rating is None and product.review_count is None


def test_vn_pdp_does_not_convert_foreign_currency(vn_router):
    router_component(vn_router)['component_data']['product_info']['price']['currency'] = 'USD'
    product = parse_vn_router(vn_router)
    assert product.price is None and product.original_price is None


@pytest.mark.parametrize('invalid', ['identity', 'error', 'region', 'component', 'page'])
def test_vn_pdp_rejects_unverified_or_non_product_components(vn_router, invalid):
    page = next(iter(vn_router['loaderData'].values()))
    component = router_component(vn_router)
    if invalid == 'identity':
        component['component_data']['product_info']['product_id'] = '999999'
    elif invalid == 'error':
        component['component_data']['error_code'] = 1
    elif invalid == 'region':
        page['region_info']['sale_region'] = 'US'
    elif invalid == 'component':
        component['component_name'] = 'recommendation'
    else:
        page['page_config']['global_fe_config']['page_name'] = 'search'
    assert parse_vn_router(vn_router) is None


@pytest.mark.parametrize('embedded', ['{broken', 'null', '[]', '{"loaderData":null}'])
def test_vn_pdp_malformed_payload_is_not_a_product(embedded):
    assert extract_product_from_html('<script id="__MODERN_ROUTER_DATA__">' + embedded + '</script>',
        'https://shop.tiktok.com/vn/pdp/1737036472084039604') is None

import json
import time
import pytest
import httpx
from app.collectors.tiktok_shop.session import sanitize_state, save_state, load_state, http_cookies, SessionStateError


def cookie(domain='.tiktok.com', expires=-1):
    return dict(name='test_session', value='fixture-secret', domain=domain,
                path='/view', expires=expires, secure=True, httpOnly=True, sameSite='Lax')


def test_filter_expired_foreign_and_credentials_origins():
    state = sanitize_state({'cookies': [cookie(), cookie('evil.test'), cookie(expires=time.time()-1)],
        'origins': [{'origin': 'https://www.tiktok.com', 'localStorage': [{'name': 'key', 'value': 'fixture'}]},
                    {'origin': 'https://www.tiktok.com.evil.test', 'localStorage': []},
                    {'origin': 'https://user:pass@www.tiktok.com', 'localStorage': []}]})
    assert len(state['cookies']) == 1 and len(state['origins']) == 1
    assert state['cookies'][0]['domain'] == '.tiktok.com'
    assert state['cookies'][0]['path'] == '/view'


def test_cookie_scope_secure_and_expiry_remain_enforced():
    state = sanitize_state({'cookies': [cookie(expires=time.time()+3600)]})
    with httpx.Client(cookies=http_cookies(state)) as client:
        assert 'fixture-secret' in client.build_request('GET', 'https://shop.tiktok.com/view/product/123').headers['cookie']
        for url in ('https://evil.test/view/product/123', 'https://shop.tiktok.com/search',
                    'http://shop.tiktok.com/view/product/123'):
            assert 'cookie' not in client.build_request('GET', url).headers
    saved = list(http_cookies(state).jar)[0]
    assert saved.expires > time.time() and saved.secure


def test_missing_invalid_and_oversize_session_do_not_leak_content(tmp_path):
    path = tmp_path/'state.json'
    assert load_state(path) is None
    for text in ('{"fixture-secret": invalid}', json.dumps({'cookies': 'fixture-secret'}), 'x'*2_000_001):
        path.write_text(text, encoding='utf-8')
        with pytest.raises(SessionStateError) as error:
            load_state(path)
        assert 'fixture-secret' not in str(error.value)


def test_save_is_filtered_and_failed_save_preserves_previous(tmp_path):
    path = tmp_path/'state.json'
    save_state({'cookies': [cookie(), cookie('other.test')]}, path)
    assert len(load_state(path)['cookies']) == 1
    original = path.read_bytes()
    with pytest.raises(ValueError):
        save_state({'cookies': 'invalid'}, path)
    assert path.read_bytes() == original
    assert not path.with_suffix('.tmp').exists()


@pytest.mark.asyncio
async def test_http_client_loads_current_session_without_browser(monkeypatch):
    from app.collectors.tiktok_shop import client as module
    state = sanitize_state({'cookies': [cookie()]})
    monkeypatch.setattr(module, 'load_state', lambda: state)
    client = module.TikTokHttpClient()
    http = await client.get_client()
    assert 'fixture-secret' in http.build_request('GET', 'https://shop.tiktok.com/view/product/123').headers['cookie']
    await client.close()


@pytest.mark.parametrize('state,expected', [(None,'missing'),({'cookies':[],'origins':[]},'missing'),
    ({'cookies':[cookie()],'origins':[]},'available')])
def test_status_exposes_only_availability(monkeypatch,state,expected):
    from app.collectors.tiktok_shop import session
    monkeypatch.setattr(session, 'load_state', lambda: state)
    assert session.session_status() == expected


def test_invalid_status_remains_readable(monkeypatch):
    from app.collectors.tiktok_shop import session
    def invalid():
        raise SessionStateError('fixture-secret')
    monkeypatch.setattr(session, 'load_state', invalid)
    assert session.session_status() == 'invalid'

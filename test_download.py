# -*- coding: utf-8 -*-
"""
マリオ・ドラクエ・妖怪ウォッチの画像を各Wikiから安全にローカル保存するテストスクリプト
"""
import requests
import os

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}

def get_wiki_image_url(wiki_api, file_title, referer_domain):
    try:
        params = {
            'action': 'query',
            'titles': f'File:{file_title}',
            'prop': 'imageinfo',
            'iiprop': 'url',
            'format': 'json'
        }
        headers = dict(HEADERS)
        headers['Referer'] = f'https://{referer_domain}/'
        r = requests.get(wiki_api, params=params, headers=headers, timeout=10)
        pages = r.json().get('query', {}).get('pages', {})
        for _, page in pages.items():
            info = page.get('imageinfo')
            if info and len(info) > 0:
                return info[0].get('url')
    except Exception as e:
        print(f"Error fetching URL for {file_title}: {e}")
    return None

def download_image(url, out_path, referer_domain):
    try:
        headers = dict(HEADERS)
        headers['Referer'] = f'https://{referer_domain}/'
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200 and len(r.content) > 1000:
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            with open(out_path, 'wb') as f:
                f.write(r.content)
            print(f"[OK] {os.path.basename(out_path)} ({len(r.content)} bytes)")
            return True
        else:
            print(f"[FAIL] status {r.status_code} for {url}")
    except Exception as e:
        print(f"[ERROR] {e}")
    return False

# テスト: 妖怪ウォッチのジバニャン & コマさん
print("--- 妖怪ウォッチ テスト ---")
jibanyan_url = get_wiki_image_url("https://yokaiwatch.fandom.com/api.php", "Jibanyan.png", "yokaiwatch.fandom.com")
print("Jibanyan URL:", jibanyan_url)
if jibanyan_url:
    download_image(jibanyan_url, "static/images/yokai/jibanyan.png", "yokaiwatch.fandom.com")

komasan_url = get_wiki_image_url("https://yokaiwatch.fandom.com/api.php", "Komasan.png", "yokaiwatch.fandom.com")
print("Komasan URL:", komasan_url)
if komasan_url:
    download_image(komasan_url, "static/images/yokai/komasan.png", "yokaiwatch.fandom.com")

# テスト: ドラクエのスライム & キングスライム
print("--- ドラクエ テスト ---")
slime_url = get_wiki_image_url("https://dragonquest.fandom.com/api.php", "Slime_Artwork.png", "dragonquest.fandom.com")
print("Slime URL:", slime_url)
if slime_url:
    download_image(slime_url, "static/images/dq/slime.png", "dragonquest.fandom.com")

# テスト: マリオ & クッパ
print("--- マリオ テスト ---")
mario_url = get_wiki_image_url("https://mario.fandom.com/api.php", "Mario_Party_Superstars_Mario.png", "mario.fandom.com")
if not mario_url:
    mario_url = "https://www.smashbros.com/assets_v2/img/fighter/mario/main.png"
print("Mario URL:", mario_url)
download_image(mario_url, "static/images/mario/mario.png", "www.smashbros.com")

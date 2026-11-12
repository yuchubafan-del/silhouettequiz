# -*- coding: utf-8 -*-
"""
MediaWiki画像検索を使って残りのキャラクター画像をすべて自動取得するスクリプト
"""
import requests
import os
import sqlite3

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}

def search_and_download(wiki_api, query, out_path, referer):
    if os.path.exists(out_path) and os.path.getsize(out_path) > 2000:
        return True
    try:
        params = {
            'action': 'query',
            'list': 'search',
            'srsearch': query,
            'srnamespace': 6,
            'format': 'json'
        }
        headers = dict(HEADERS)
        headers['Referer'] = f'https://{referer}/'
        r = requests.get(wiki_api, params=params, headers=headers, timeout=10).json()
        items = r.get('query', {}).get('search', [])
        for it in items[:4]:
            title = it['title']
            if not any(ext in title.lower() for ext in ['.png', '.webp', '.jpg']):
                continue
            p_info = requests.get(wiki_api, params={'action': 'query', 'titles': title, 'prop': 'imageinfo', 'iiprop': 'url', 'format': 'json'}, headers=headers, timeout=10).json()
            pages = p_info.get('query', {}).get('pages', {})
            for _, p in pages.items():
                info = p.get('imageinfo')
                if info and len(info) > 0:
                    iurl = info[0]['url']
                    ir = requests.get(iurl, headers=headers, timeout=15)
                    if ir.status_code == 200 and len(ir.content) > 1000:
                        os.makedirs(os.path.dirname(out_path), exist_ok=True)
                        with open(out_path, 'wb') as f:
                            f.write(ir.content)
                        print(f"  [GET] {os.path.basename(out_path)} from {title} ({len(ir.content)} bytes)")
                        return True
    except Exception as e:
        print(f"  [ERR] {query}: {e}")
    return False

# マリオ残分
mario_queries = [
    ("waluigi.png", "Waluigi render png"),
    ("rosalina.png", "Rosalina render png"),
    ("bowser_jr.png", "Bowser Jr render png"),
    ("koopa_troopa.png", "Koopa Troopa render png"),
    ("boo.png", "Boo render png"),
    ("bob_omb.png", "Bob-omb render png"),
    ("shy_guy.png", "Shy Guy render png"),
    ("kamek.png", "Kamek render png"),
    ("thwomp.png", "Thwomp render png"),
    ("chain_chomp.png", "Chain Chomp render png"),
    ("bullet_bill.png", "Bullet Bill render png"),
    ("birdo.png", "Birdo render png"),
    ("spiny.png", "Spiny render png")
]

print("=== マリオキャラクター検索取得中 ===")
for fname, q in mario_queries:
    out = f"static/images/mario/{fname}"
    search_and_download("https://www.mariowiki.com/api.php", q, out, "www.mariowiki.com")

# ドラクエ残分
dq_queries = [
    ("liquid_metal_slime.png", "Liquid Metal Slime Artwork"),
    ("metal_king_slime.png", "Metal King Slime Artwork"),
    ("metal_slime.png", "Metal Slime Artwork"),
    ("killing_machine.png", "Killing Machine Artwork"),
    ("bomboulder.png", "Bomboulder Artwork"),
    ("green_dragon.png", "Green Dragon Artwork"),
    ("dragonlord.png", "Dragonlord Artwork"),
    ("psaro.png", "Psaro Artwork"),
    ("estark.png", "Estark Artwork"),
    ("stump_chump.png", "Stump Chump Artwork"),
    ("spookstool.png", "Spookstool Artwork"),
    ("platypunk.png", "Platypunk Artwork"),
    ("restless_armour.png", "Restless Armour Artwork")
]

print("\n=== ドラクエキャラクター検索取得中 ===")
for fname, q in dq_queries:
    out = f"static/images/dq/{fname}"
    search_and_download("https://dragonquest.fandom.com/api.php", q, out, "dragonquest.fandom.com")

# 妖怪ウォッチ ぬらりひょん
print("\n=== 妖怪ウォッチ残分検索取得中 ===")
search_and_download("https://yokaiwatch.fandom.com/api.php", "Zazel png", "static/images/yokai/zazel.png", "yokaiwatch.fandom.com")

print("\n全取得完了！")

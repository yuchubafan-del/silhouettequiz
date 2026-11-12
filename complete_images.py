# -*- coding: utf-8 -*-
"""
マリオ・ドラクエの残りキャラクターの画像を確実にダウンロードするスクリプト
"""
import requests
import os

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

DOWNLOAD_TARGETS = [
    # マリオ (任天堂公式スマブラCDN)
    ("static/images/mario/luigi.png", "https://www.smashbros.com/assets_v2/img/fighter/luigi/main.png", "www.smashbros.com"),
    ("static/images/mario/bowser.png", "https://www.smashbros.com/assets_v2/img/fighter/koopa/main.png", "www.smashbros.com"),
    ("static/images/mario/peach.png", "https://www.smashbros.com/assets_v2/img/fighter/peach/main.png", "www.smashbros.com"),
    ("static/images/mario/yoshi.png", "https://www.smashbros.com/assets_v2/img/fighter/yoshi/main.png", "www.smashbros.com"),
    ("static/images/mario/daisy.png", "https://www.smashbros.com/assets_v2/img/fighter/daisy/main.png", "www.smashbros.com"),
    ("static/images/mario/wario.png", "https://www.smashbros.com/assets_v2/img/fighter/wario/main.png", "www.smashbros.com"),
    ("static/images/mario/rosalina.png", "https://www.smashbros.com/assets_v2/img/fighter/rosetta/main.png", "www.smashbros.com"),
    ("static/images/mario/bowser_jr.png", "https://www.smashbros.com/assets_v2/img/fighter/koopajr/main.png", "www.smashbros.com"),
    ("static/images/mario/donkey_kong.png", "https://www.smashbros.com/assets_v2/img/fighter/donkey_kong/main.png", "www.smashbros.com"),
    ("static/images/mario/diddy_kong.png", "https://www.smashbros.com/assets_v2/img/fighter/diddy_kong/main.png", "www.smashbros.com"),
    ("static/images/mario/piranha_plant.png", "https://www.smashbros.com/assets_v2/img/fighter/packun_flower/main.png", "www.smashbros.com"),
]

for out_path, url, referer in DOWNLOAD_TARGETS:
    if os.path.exists(out_path) and os.path.getsize(out_path) > 2000:
        continue
    try:
        headers = dict(HEADERS)
        headers['Referer'] = f'https://{referer}/'
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200 and len(r.content) > 1000:
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            with open(out_path, 'wb') as f:
                f.write(r.content)
            print(f"[OK] {os.path.basename(out_path)} ({len(r.content)} bytes)")
        else:
            print(f"[FAIL {r.status_code}] {url}")
    except Exception as e:
        print(f"[ERR] {e}")

# さらにMario Wiki APIから直接URL解決
mario_wiki_extras = [
    ("toad.png", "Toad_-_Mario_Party_10.png"),
    ("waluigi.png", "Waluigi_-_Mario_Party_10.png"),
    ("goomba.png", "Goomba_-_Mario_Party_10.png"),
    ("koopa_troopa.png", "KoopaTroopa_-_Mario_Party_10.png"),
    ("boo.png", "Boo_-_Mario_Party_10.png"),
    ("bob_omb.png", "Bob-omb_MP10.png"),
    ("shy_guy.png", "ShyGuy_-_Mario_Party_10.png"),
    ("kamek.png", "Kamek_-_Mario_Party_10.png"),
    ("thwomp.png", "Thwomp_-_Mario_Party_10.png"),
    ("bullet_bill.png", "BulletBill_-_Mario_Party_10.png"),
    ("chain_chomp.png", "ChainChomp_-_Mario_Party_10.png"),
    ("spiny.png", "Spiny_NSMBU.png"),
    ("toadette.png", "Toadette_-_Mario_Party_10.png"),
    ("birdo.png", "Birdo_-_Mario_Party_9.png"),
]

for fname, title in mario_wiki_extras:
    out_path = f"static/images/mario/{fname}"
    if os.path.exists(out_path) and os.path.getsize(out_path) > 2000:
        continue
    try:
        api = "https://www.mariowiki.com/api.php"
        params = {'action': 'query', 'titles': f'File:{title}', 'prop': 'imageinfo', 'iiprop': 'url', 'format': 'json'}
        r = requests.get(api, params=params, headers=HEADERS, timeout=8).json()
        pages = r.get('query', {}).get('pages', {})
        for _, p in pages.items():
            info = p.get('imageinfo')
            if info:
                iurl = info[0]['url']
                ir = requests.get(iurl, headers={'User-Agent': HEADERS['User-Agent'], 'Referer': 'https://www.mariowiki.com/'}, timeout=10)
                if ir.status_code == 200 and len(ir.content) > 1000:
                    with open(out_path, 'wb') as f:
                        f.write(ir.content)
                    print(f"[OK Mario Wiki] {fname} ({len(ir.content)} bytes)")
    except Exception as e:
        print(f"[ERR Mario Wiki] {fname}: {e}")

# ドラクエの追加分
dq_extras = [
    ("king_slime.png", "King_slime_Artwork.png"),
    ("liquid_metal_slime.png", "Liquid_metal_slime_Artwork.png"),
    ("metal_king_slime.png", "Metal_king_slime_Artwork.png"),
    ("metal_slime.png", "Metal_slime_Artwork.png"),
    ("killing_machine.png", "Killing_machine_Artwork.png"),
    ("bomboulder.png", "Bomboulder_Artwork.png"),
    ("green_dragon.png", "Green_dragon_Artwork.png"),
    ("dragonlord.png", "Dragonlord_true_form_Artwork.png"),
    ("psaro.png", "Psaro_the_Manslayer_Artwork.png"),
    ("estark.png", "Estark_Artwork.png"),
    ("stump_chump.png", "Stump_chump_Artwork.png"),
    ("spookstool.png", "Spookstool_Artwork.png"),
    ("platypunk.png", "Platypunk_Artwork.png"),
    ("restless_armour.png", "Restless_armour_Artwork.png")
]

for fname, title in dq_extras:
    out_path = f"static/images/dq/{fname}"
    if os.path.exists(out_path) and os.path.getsize(out_path) > 2000:
        continue
    try:
        api = "https://dragonquest.fandom.com/api.php"
        params = {'action': 'query', 'titles': f'File:{title}', 'prop': 'imageinfo', 'iiprop': 'url', 'format': 'json'}
        r = requests.get(api, params=params, headers=HEADERS, timeout=8).json()
        pages = r.get('query', {}).get('pages', {})
        for _, p in pages.items():
            info = p.get('imageinfo')
            if info:
                iurl = info[0]['url']
                ir = requests.get(iurl, headers={'User-Agent': HEADERS['User-Agent'], 'Referer': 'https://dragonquest.fandom.com/'}, timeout=10)
                if ir.status_code == 200 and len(ir.content) > 1000:
                    with open(out_path, 'wb') as f:
                        f.write(ir.content)
                    print(f"[OK DQ Fandom] {fname} ({len(ir.content)} bytes)")
    except Exception as e:
        print(f"[ERR DQ] {fname}: {e}")

print("完了！")

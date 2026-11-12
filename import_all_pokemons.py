# -*- coding: utf-8 -*-
"""
全世代ポケモン（第1〜9世代） + メガシンカ + キョダイマックス + ゲンシカイキ
の公式データをPokeAPIのCSVリポジトリから一括インポートして pokemon_quiz.db を更新するスクリプト
"""
import sqlite3
import csv
import io
import os
import requests

DB_PATH = os.path.join(os.path.dirname(__file__), "pokemon_quiz.db")
BASE_URL = "https://raw.githubusercontent.com/PokeAPI/pokeapi/master/data/v2/csv"

def fetch_csv(filename):
    url = f"{BASE_URL}/{filename}"
    print(f"ダウンロード中: {filename}...")
    r = requests.get(url, timeout=30)
    r.encoding = "utf-8"
    return list(csv.DictReader(io.StringIO(r.text)))

def build_database():
    print("=== PokeAPI公式CSVデータのダウンロードと解析を開始します ===")

    types_csv = fetch_csv("types.csv")
    type_names_csv = fetch_csv("type_names.csv")
    pokemon_types_csv = fetch_csv("pokemon_types.csv")
    species_csv = fetch_csv("pokemon_species.csv")
    species_names_csv = fetch_csv("pokemon_species_names.csv")
    pokemon_csv = fetch_csv("pokemon.csv")

    type_map = {}
    for row in type_names_csv:
        if row["local_language_id"] == "1":
            type_map[row["type_id"]] = row["name"]

    pokemon_type_map = {}
    for row in pokemon_types_csv:
        pid = row["pokemon_id"]
        if pid not in pokemon_type_map:
            pokemon_type_map[pid] = [None, None]
        slot = int(row["slot"]) - 1
        tname = type_map.get(row["type_id"], "ノーマル")
        if slot < 2:
            pokemon_type_map[pid][slot] = tname

    species_gen_map = {}
    for row in species_csv:
        species_gen_map[row["id"]] = int(row["generation_id"] or 1)

    species_name_map = {}
    for row in species_names_csv:
        if row["local_language_id"] == "1":
            species_name_map[row["pokemon_species_id"]] = (row["name"], row["genus"])

    pokemons_to_insert = []
    
    for row in pokemon_csv:
        pid = int(row["id"])
        sid = row["species_id"]
        ident = row["identifier"]
        is_default = row["is_default"] == "1"

        base_info = species_name_map.get(sid, (ident.capitalize(), "ポケモン"))
        base_name_ja, genus = base_info
        gen = species_gen_map.get(sid, 1)

        types = pokemon_type_map.get(str(pid), ["ノーマル", None])
        type1, type2 = types[0] or "ノーマル", types[1]

        form_type = "normal"
        name_ja = base_name_ja
        name_en = ident.replace("-", " ").title()
        flavor_text = f"全国図鑑 No.{sid}。{genus}。"
        aliases = [name_ja, name_en.lower()]

        # 1. 通常ポケモン (is_default == 1)
        if is_default:
            form_type = "normal"
            name_ja = base_name_ja

        # 2. メガシンカ (ident が '-mega' を含む)
        elif "-mega" in ident:
            form_type = "mega"
            if ident.endswith("-x"):
                name_ja = f"メガ{base_name_ja}X"
                aliases = [name_ja, f"メガ{base_name_ja}エックス", f"{base_name_ja}メガシンカX", name_en.lower()]
            elif ident.endswith("-y"):
                name_ja = f"メガ{base_name_ja}Y"
                aliases = [name_ja, f"メガ{base_name_ja}ワイ", f"{base_name_ja}メガシンカY", name_en.lower()]
            else:
                name_ja = f"メガ{base_name_ja}"
                aliases = [name_ja, f"{base_name_ja}メガシンカ", f"メガ{base_name_ja}", name_en.lower()]
            flavor_text = f"{base_name_ja}がメガシンカした姿！秘められたパワーが覚醒した。"

        # 3. キョダイマックス (ident が '-gmax' を含む)
        elif "-gmax" in ident:
            form_type = "gmax"
            name_ja = f"キョダイマックス{base_name_ja}"
            aliases = [name_ja, f"キョダイ{base_name_ja}", f"{base_name_ja}キョダイマックス", name_en.lower()]
            flavor_text = f"{base_name_ja}がキョダイマックスした巨大な姿！専用のキョダイマックスわざを放つ。"

        # 4. ゲンシカイキ
        elif ident in ("kyogre-primal", "groudon-primal"):
            form_type = "primal"
            name_ja = f"ゲンシ{base_name_ja}"
            aliases = [name_ja, f"{base_name_ja}ゲンシカイキ", name_en.lower()]
            flavor_text = f"自然のエネルギーによって本来の真の姿を取り戻した古代の姿。"

        else:
            continue

        image_url = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/{pid}.png"

        pokemons_to_insert.append({
            "id": pid,
            "species_id": int(sid),
            "identifier": ident,
            "name_ja": name_ja,
            "name_en": name_en,
            "base_name_ja": base_name_ja,
            "form_type": form_type,
            "type1": type1,
            "type2": type2,
            "genus": genus,
            "flavor_text": flavor_text,
            "image_url": image_url,
            "generation": gen,
            "aliases": ",".join(set(aliases))
        })

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS pokemons;")
    cursor.execute("""
    CREATE TABLE pokemons (
        id INTEGER PRIMARY KEY,
        species_id INTEGER,
        identifier TEXT,
        name_ja TEXT NOT NULL,
        name_en TEXT NOT NULL,
        base_name_ja TEXT,
        form_type TEXT DEFAULT 'normal',
        type1 TEXT NOT NULL,
        type2 TEXT,
        genus TEXT,
        flavor_text TEXT,
        image_url TEXT NOT NULL,
        generation INTEGER DEFAULT 1,
        aliases TEXT
    );
    """)

    for p in pokemons_to_insert:
        cursor.execute("""
        INSERT INTO pokemons
        (id, species_id, identifier, name_ja, name_en, base_name_ja, form_type, type1, type2, genus, flavor_text, image_url, generation, aliases)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            p["id"], p["species_id"], p["identifier"], p["name_ja"], p["name_en"],
            p["base_name_ja"], p["form_type"], p["type1"], p["type2"], p["genus"],
            p["flavor_text"], p["image_url"], p["generation"], p["aliases"]
        ))

    conn.commit()
    cursor.execute("SELECT COUNT(*) FROM pokemons")
    total_db = cursor.fetchone()[0]
    conn.close()

    print(f"=== [完了] データベース更新完了！ 合計: {total_db} 匹が登録されました ===")

if __name__ == "__main__":
    build_database()

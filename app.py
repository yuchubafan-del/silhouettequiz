# -*- coding: utf-8 -*-
"""
キャラクター シルエットクイズ 総合Webアプリケーションサーバー
【ポケモン / 妖怪ウォッチ / ドラゴンクエスト / スーパーマリオ / オールスター】
Flask + SQLite
"""
import os
import sqlite3
import random
import re
import unicodedata
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__, static_folder="static")
DB_PATH = os.path.join(os.path.dirname(__file__), "pokemon_quiz.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def normalize_text(text):
    """ひらがな・カタカナ・全角半角のゆらぎを正規化"""
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", text).strip().lower()
    text = "".join([chr(ord(c) + 96) if "ぁ" <= c <= "ん" else c for c in text])
    text = re.sub(r"[\s・\-\_ー\.\,]", "", text)
    return text

@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/<path:path>")
def static_proxy(path):
    return send_from_directory("static", path)

# -------------------------------------------------------------
# 1. クイズ出題 API (マルチモード対応)
# -------------------------------------------------------------
@app.route("/api/quiz/question", methods=["GET"])
def get_quiz_question():
    category = request.args.get("category", "pokemon")  # 'all', 'pokemon', 'yokai', 'dq', 'mario'
    form_filter = request.args.get("form", "all")      # ポケモン用: 'all', 'normal', 'mega', 'gmax'

    conn = get_db()
    cursor = conn.cursor()

    query = """
        SELECT id, category, identifier, name_ja, name_en, form_type,
               attribute1, attribute2, genus, flavor_text, image_url, generation, aliases
        FROM characters
    """
    conditions = []
    params = []

    if category != "all":
        conditions.append("category = ?")
        params.append(category)

        # ポケモンの場合のフォーム絞り込み
        if category == "pokemon" and form_filter in ("normal", "mega", "gmax"):
            conditions.append("form_type = ?")
            params.append(form_filter)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY RANDOM() LIMIT 1"
    cursor.execute(query, params)
    target = cursor.fetchone()

    if not target:
        conn.close()
        return jsonify({"error": "No character found"}), 404

    # ヒント用の説明文から名前を伏せ字化
    masked_flavor = target["flavor_text"] or ""
    hide_words = [target["name_ja"]]
    if "メガ" in target["name_ja"]:
        hide_words.append(target["name_ja"].replace("メガ", ""))
    if "キョダイマックス" in target["name_ja"]:
        hide_words.append(target["name_ja"].replace("キョダイマックス", ""))

    for hide in hide_words:
        if hide and len(hide) >= 2:
            masked_flavor = masked_flavor.replace(hide, "◯◯◯◯")
            if len(hide) >= 3:
                masked_flavor = masked_flavor.replace(hide[:len(hide)-1], "◯◯◯")

    cat = target["category"]
    
    # カテゴリごとのラベル・バナーカスタマイズ
    cat_meta = {
        "pokemon": {
            "title": "ポケモン",
            "banner": "「この ポケモン だ〜れだ？」",
            "attr1_label": "タイプ",
            "genus_label": "分類",
            "flavor_label": "図鑑説明",
            "badge_icon": "🔴"
        },
        "yokai": {
            "title": "妖怪ウォッチ",
            "banner": "「この ようかい だ〜れだ？」",
            "attr1_label": "種族",
            "genus_label": "妖怪の特徴",
            "flavor_label": "大辞典の説明",
            "badge_icon": "👻"
        },
        "dq": {
            "title": "ドラゴンクエスト",
            "banner": "「この まもの だ〜れだ？」",
            "attr1_label": "系統",
            "genus_label": "まものの分類",
            "flavor_label": "討伐モンスター図鑑",
            "badge_icon": "⚔️"
        },
        "mario": {
            "title": "スーパーマリオ",
            "banner": "「この キャラ だ〜れだ？」",
            "attr1_label": "陣営・タイプ",
            "genus_label": "肩書き・特徴",
            "flavor_label": "キャラクター解説",
            "badge_icon": "🍄"
        }
    }
    meta = cat_meta.get(cat, cat_meta["pokemon"])

    # 姿のヒント
    form_hint = "通常"
    if target["form_type"] == "mega": form_hint = "メガシンカ"
    elif target["form_type"] == "gmax": form_hint = "キョダイマックス"
    elif target["form_type"] == "primal": form_hint = "ゲンシカイキ"

    response_data = {
        "character_id": target["id"],
        "category": cat,
        "form_type": target["form_type"],
        "image_url": target["image_url"],
        "meta": meta,
        "hints": {
            "form_hint": form_hint,
            "attribute1": target["attribute1"],
            "attribute2": target["attribute2"],
            "genus": target["genus"],
            "flavor_text": masked_flavor
        }
    }

    conn.close()
    return jsonify(response_data)

# -------------------------------------------------------------
# 2. クイズ回答判定 API
# -------------------------------------------------------------
@app.route("/api/quiz/answer", methods=["POST"])
def check_quiz_answer():
    data = request.get_json() or {}
    char_id = data.get("character_id")
    chosen_name = (data.get("chosen_name") or "").strip()
    hints_used = int(data.get("hints_used", 0))
    time_taken_ms = int(data.get("time_taken_ms", 0))
    current_streak = int(data.get("current_streak", 0))

    if not char_id:
        return jsonify({"error": "Missing character_id"}), 400

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, category, identifier, name_ja, name_en, form_type,
               attribute1, attribute2, genus, flavor_text, image_url, aliases
        FROM characters
        WHERE id = ?
    """, (char_id,))
    target = cursor.fetchone()

    if not target:
        conn.close()
        return jsonify({"error": "Character not found"}), 404

    user_norm = normalize_text(chosen_name)
    target_norm = normalize_text(target["name_ja"])

    valid_names = [target_norm]
    if target["aliases"]:
        for a in target["aliases"].split(","):
            valid_names.append(normalize_text(a))

    is_correct = user_norm in valid_names

    # 惜しい判定
    almost = False
    almost_message = ""
    if not is_correct:
        # メガ・キョダイマックスで通常名のみ答えた場合
        if target["form_type"] in ("mega", "gmax", "primal"):
            base_cand = target["name_ja"].replace("メガ", "").replace("キョダイマックス", "").replace("ゲンシ", "").replace("X", "").replace("Y", "")
            if user_norm == normalize_text(base_cand):
                almost = True
                almost_message = f"💡 おしい！「メガ」や「キョダイマックス」の姿だったよ！"
        # スライム系で「スライム」と答えた場合
        elif "スライム" in target["name_ja"] and user_norm == normalize_text("スライム") and target["name_ja"] != "スライム":
            almost = True
            almost_message = f"💡 おしい！ただのスライムじゃなくて「{target['name_ja']}」だよ！"

    # スコア計算
    earned_score = 0
    if is_correct:
        base_score = 1200
        if target["form_type"] in ("mega", "gmax", "primal"):
            base_score += 300
        hint_penalty = hints_used * 150
        seconds = max(0, (time_taken_ms - 3000) / 1000.0)
        time_penalty = min(400, int(seconds * 25))
        streak_bonus = current_streak * 120
        earned_score = max(300, base_score - hint_penalty - time_penalty + streak_bonus)

        # player_collection に保存
        cursor.execute("""
            INSERT INTO player_collection (character_id, category, captured_count, first_captured_at, last_captured_at)
            VALUES (?, ?, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT(character_id) DO UPDATE SET
                captured_count = captured_count + 1,
                last_captured_at = CURRENT_TIMESTAMP
        """, (target["id"], target["category"]))

    # quiz_logs に記録
    cursor.execute("""
        INSERT INTO quiz_logs (pokemon_id, chosen_name, is_correct, hints_used, time_taken_ms)
        VALUES (?, ?, ?, ?, ?)
    """, (target["id"], chosen_name, 1 if is_correct else 0, hints_used, time_taken_ms))

    conn.commit()

    # コレクション回数取得
    cursor.execute("SELECT captured_count FROM player_collection WHERE character_id = ?", (target["id"],))
    coll_entry = cursor.fetchone()
    captured_count = coll_entry["captured_count"] if coll_entry else 0

    conn.close()

    return jsonify({
        "is_correct": is_correct,
        "almost": almost,
        "almost_message": almost_message,
        "earned_score": earned_score,
        "character": {
            "id": target["id"],
            "category": target["category"],
            "name_ja": target["name_ja"],
            "name_en": target["name_en"],
            "form_type": target["form_type"],
            "attribute1": target["attribute1"],
            "attribute2": target["attribute2"],
            "genus": target["genus"],
            "flavor_text": target["flavor_text"],
            "image_url": target["image_url"],
            "captured_count": captured_count
        }
    })

# -------------------------------------------------------------
# 3. キャラクター名サジェスト API
# -------------------------------------------------------------
@app.route("/api/character/names", methods=["GET"])
def get_character_names():
    category = request.args.get("category", "all")
    conn = get_db()
    cursor = conn.cursor()

    if category == "all":
        cursor.execute("SELECT DISTINCT name_ja FROM characters ORDER BY id ASC")
    else:
        cursor.execute("SELECT DISTINCT name_ja FROM characters WHERE category = ? ORDER BY id ASC", (category,))

    names = [r["name_ja"] for r in cursor.fetchall()]
    conn.close()
    return jsonify({"names": names})

# -------------------------------------------------------------
# 4. 図鑑 / コレクション一覧 API (カテゴリ別)
# -------------------------------------------------------------
@app.route("/api/collection", methods=["GET"])
def get_collection():
    category = request.args.get("category", "pokemon")
    conn = get_db()
    cursor = conn.cursor()

    query = """
        SELECT
            c.id, c.category, c.identifier, c.name_ja, c.name_en, c.form_type,
            c.attribute1, c.attribute2, c.genus, c.flavor_text, c.image_url, c.generation,
            COALESCE(pc.captured_count, 0) AS captured_count,
            pc.first_captured_at,
            pc.last_captured_at
        FROM characters c
        LEFT JOIN player_collection pc ON c.id = pc.character_id
    """
    params = []
    if category != "all":
        query += " WHERE c.category = ?"
        params.append(category)

    query += " ORDER BY c.id ASC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    char_list = [dict(r) for r in rows]

    total_count = len(char_list)
    captured_total = sum(1 for c in char_list if c["captured_count"] > 0)
    completion_rate = round((captured_total / total_count * 100), 1) if total_count > 0 else 0

    conn.close()
    return jsonify({
        "category": category,
        "total": total_count,
        "captured": captured_total,
        "completion_rate": completion_rate,
        "characters": char_list
    })

# -------------------------------------------------------------
# 5. ランキング (リーダーボード) API
# -------------------------------------------------------------
@app.route("/api/leaderboard", methods=["GET", "POST"])
def leaderboard_api():
    conn = get_db()
    cursor = conn.cursor()

    if request.method == "POST":
        data = request.get_json() or {}
        player_name = (data.get("player_name") or "名無しプレイヤー").strip()[:20]
        score = int(data.get("score", 0))
        correct_count = int(data.get("correct_count", 0))
        max_streak = int(data.get("max_streak", 0))
        category = data.get("category", "pokemon")
        difficulty = f"手入力({category})"

        cursor.execute("""
            INSERT INTO leaderboard (player_name, score, correct_count, max_streak, difficulty)
            VALUES (?, ?, ?, ?, ?)
        """, (player_name, score, correct_count, max_streak, difficulty))
        conn.commit()
        entry_id = cursor.lastrowid
        conn.close()
        return jsonify({"success": True, "entry_id": entry_id})

    cursor.execute("""
        SELECT id, player_name, score, correct_count, max_streak, difficulty,
               strftime('%Y/%m/%d %H:%M', created_at, 'localtime') as created_at_jp
        FROM leaderboard
        ORDER BY score DESC, created_at ASC
        LIMIT 20
    """)
    leaderboard = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return jsonify({"leaderboard": leaderboard})

# -------------------------------------------------------------
# 6. ゲーム統計 API
# -------------------------------------------------------------
@app.route("/api/stats", methods=["GET"])
def get_stats():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            COUNT(*) as total_answers,
            COALESCE(SUM(is_correct), 0) as correct_answers,
            COALESCE(AVG(hints_used), 0) as avg_hints,
            COALESCE(AVG(time_taken_ms), 0) as avg_time_ms
        FROM quiz_logs
    """)
    summary_row = cursor.fetchone()
    total_answers = summary_row["total_answers"]
    correct_answers = summary_row["correct_answers"]
    accuracy = round((correct_answers / total_answers * 100), 1) if total_answers > 0 else 0

    cursor.execute("""
        SELECT c.name_ja, c.category, COUNT(*) as correct_count
        FROM quiz_logs q
        JOIN characters c ON q.pokemon_id = c.id
        WHERE q.is_correct = 1
        GROUP BY c.id
        ORDER BY correct_count DESC
        LIMIT 5
    """)
    top_correct = [dict(r) for r in cursor.fetchall()]

    cursor.execute("""
        SELECT c.name_ja, c.category, COUNT(*) as wrong_count
        FROM quiz_logs q
        JOIN characters c ON q.pokemon_id = c.id
        WHERE q.is_correct = 0
        GROUP BY c.id
        ORDER BY wrong_count DESC
        LIMIT 5
    """)
    top_wrong = [dict(r) for r in cursor.fetchall()]

    conn.close()
    return jsonify({
        "total_answers": total_answers,
        "correct_answers": correct_answers,
        "accuracy_percent": accuracy,
        "avg_hints": round(summary_row["avg_hints"], 1),
        "avg_time_sec": round(summary_row["avg_time_ms"] / 1000.0, 1),
        "top_correct": top_correct,
        "top_wrong": top_wrong
    })

# -------------------------------------------------------------
# 7. SQL探検コンソール API
# -------------------------------------------------------------
@app.route("/api/sql/execute", methods=["POST"])
def execute_sql():
    data = request.get_json() or {}
    query = (data.get("query") or "").strip()

    if not query:
        return jsonify({"error": "SQLクエリが空です。"}), 400

    first_word = query.split()[0].upper()
    if first_word not in ("SELECT", "PRAGMA", "EXPLAIN"):
        return jsonify({"error": "安全のため、実行できるのは SELECT / PRAGMA 文のみです。"}), 400

    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(query)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        results = [dict(r) for r in rows]
        conn.close()
        return jsonify({
            "success": True,
            "columns": columns,
            "row_count": len(results),
            "data": results[:100]
        })
    except Exception as e:
        conn.close()
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    # テーブル自動確認
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS player_collection (
        character_id INTEGER PRIMARY KEY,
        category TEXT NOT NULL,
        captured_count INTEGER DEFAULT 0,
        first_captured_at DATETIME,
        last_captured_at DATETIME,
        FOREIGN KEY (character_id) REFERENCES characters(id)
    );
    """)
    conn.commit()
    conn.close()

    print("=" * 60)
    print("キャラクター シルエットクイズ 総合サーバー起動中...")
    print("【ポケモン / 妖怪ウォッチ / ドラクエ / マリオ】対応！")
    print("ブラウザで http://127.0.0.1:5000 を開いてください")
    print("=" * 60)
    app.run(host="127.0.0.1", port=5000, debug=False)

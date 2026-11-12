# -*- coding: utf-8 -*-
import sqlite3
import requests

conn = sqlite3.connect('pokemon_quiz.db')
cursor = conn.cursor()

cursor.execute("SELECT id, name_ja FROM characters WHERE category = 'yokai' AND identifier = 'jibanyan'")
jid, jname = cursor.fetchone()

cursor.execute("SELECT id, name_ja FROM characters WHERE category = 'dq' AND identifier = 'slime'")
sid, sname = cursor.fetchone()

cursor.execute("SELECT id, name_ja FROM characters WHERE category = 'mario' AND identifier = 'bowser'")
bid, bname = cursor.fetchone()

# 1. 妖怪ウォッチ判定テスト
r1 = requests.post('http://127.0.0.1:5000/api/quiz/answer', json={'character_id': jid, 'chosen_name': 'じばにゃん', 'hints_used': 0, 'time_taken_ms': 1200, 'current_streak': 0}).json()
print('Jibanyan ->', r1['is_correct'], r1['character']['name_ja'], r1['earned_score'])

# 2. ドラクエ判定テスト
r2 = requests.post('http://127.0.0.1:5000/api/quiz/answer', json={'character_id': sid, 'chosen_name': 'すらいむ', 'hints_used': 0, 'time_taken_ms': 1100, 'current_streak': 1}).json()
print('Slime ->', r2['is_correct'], r2['character']['name_ja'], r2['earned_score'])

# 3. マリオ判定テスト
r3 = requests.post('http://127.0.0.1:5000/api/quiz/answer', json={'character_id': bid, 'chosen_name': 'くっぱ', 'hints_used': 0, 'time_taken_ms': 1300, 'current_streak': 2}).json()
print('Bowser ->', r3['is_correct'], r3['character']['name_ja'], r3['earned_score'])

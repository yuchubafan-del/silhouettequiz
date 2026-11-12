import sqlite3, json, sys
db_path = r"c:\\Users\\cre\\Desktop\\ow\\pokemon_quiz.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.execute('SELECT category, COUNT(*) FROM characters GROUP BY category')
rows = cur.fetchall()
print(json.dumps(dict(rows), ensure_ascii=False, indent=2))
conn.close()

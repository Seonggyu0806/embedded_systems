# 1차시 미션 3: SQLite 최신 N행을 직접 조회해 /api/readings 결과와 비교
# 사용: python db_latest.py [N]   (기본 5)
import sqlite3
import sys

limit = int(sys.argv[1]) if len(sys.argv) > 1 else 5
with sqlite3.connect("sensors.db") as conn:
    rows = conn.execute("""
        SELECT timestamp, temperature, humidity, status
        FROM readings ORDER BY timestamp DESC, id DESC LIMIT ?
    """, (limit,)).fetchall()
    total = conn.execute("SELECT COUNT(*) FROM readings").fetchone()[0]

print(f"readings 총 {total}행 중 최신 {len(rows)}행")
for ts, t, h, st in rows:
    print(f"{ts} | {t if t is not None else '-':>5} | {h if h is not None else '-':>5} | {st}")

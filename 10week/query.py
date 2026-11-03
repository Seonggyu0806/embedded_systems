# 10주차 2차시 미션 B: SQLite 조회
# 최신값 · 오늘 기간 조회 · 평균/최소/최대/개수
import sqlite3
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")
conn = sqlite3.connect("sensors.db")

# 오늘 [00:00, 내일 00:00) 경계
today = datetime.now(KST).replace(hour=0, minute=0, second=0, microsecond=0)
start_ts = today.isoformat(timespec="seconds")
end_ts = (today + timedelta(days=1)).isoformat(timespec="seconds")

# 1) 전체 개수
total, ok_total, err_total = conn.execute("""
SELECT COUNT(*),
       SUM(status = 'OK'),
       SUM(status = 'ERROR')
FROM readings
""").fetchone()
print(f"[전체] {total}건 (OK {ok_total} / ERROR {err_total})")

# 2) 최신 기록 (오류 포함)
row = conn.execute("""
SELECT timestamp, temperature, humidity, status, error_message
FROM readings
ORDER BY timestamp DESC, id DESC
LIMIT 1
""").fetchone()
print("\n[최신 기록]", row if row else "없음")

# 3) 최신 정상 기록
row = conn.execute("""
SELECT timestamp, temperature, humidity
FROM readings
WHERE status = 'OK'
ORDER BY timestamp DESC, id DESC
LIMIT 1
""").fetchone()
print("[최신 정상]", row if row else "없음")

# 4) 오늘 정상 기록 (시간 오름차순)
rows = conn.execute("""
SELECT timestamp, temperature, humidity
FROM readings
WHERE status = 'OK'
  AND timestamp >= ?
  AND timestamp < ?
ORDER BY timestamp ASC
""", (start_ts, end_ts)).fetchall()
print(f"\n[오늘 정상 기록] {start_ts} ~ {end_ts} : {len(rows)}건")
for r in rows[:5]:
    print("  ", r)
if len(rows) > 5:
    print(f"   ... 외 {len(rows) - 5}건")

# 5) 오늘 통계
avg_t, min_t, max_t, avg_h, count = conn.execute("""
SELECT AVG(temperature), MIN(temperature), MAX(temperature),
       AVG(humidity), COUNT(*)
FROM readings
WHERE status = 'OK'
  AND timestamp >= ?
  AND timestamp < ?
""", (start_ts, end_ts)).fetchone()
errors = conn.execute("""
SELECT COUNT(*) FROM readings
WHERE status = 'ERROR' AND timestamp >= ? AND timestamp < ?
""", (start_ts, end_ts)).fetchone()[0]

print("\n[오늘 통계]")
if count:
    print(f"  평균 온도: {avg_t:.1f} C")
    print(f"  최저/최고: {min_t:.1f} / {max_t:.1f} C")
    print(f"  평균 습도: {avg_h:.1f} %")
print(f"  정상 {count}건 / 오류 {errors}건")

conn.close()

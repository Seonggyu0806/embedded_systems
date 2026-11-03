# 10주차 2차시 미션 C: HTML 리포트 + CSV 내보내기 + 행 수 교차 검증
import csv
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")
DB_PATH = "sensors.db"
CSV_PATH = Path("environment.csv")
REPORT_DIR = Path("reports")
EXPORT_PATH = Path("daily_export.csv")

today = datetime.now(KST).replace(hour=0, minute=0, second=0, microsecond=0)
day = today.date().isoformat()
start_ts = today.isoformat(timespec="seconds")
end_ts = (today + timedelta(days=1)).isoformat(timespec="seconds")

conn = sqlite3.connect(DB_PATH)

# 1) 오늘 정상 기록 조회
rows = conn.execute("""
SELECT timestamp, temperature, humidity
FROM readings
WHERE status = 'OK' AND timestamp >= ? AND timestamp < ?
ORDER BY timestamp ASC
""", (start_ts, end_ts)).fetchall()

# 2) 통계 5개 + 오류 건수
stats = conn.execute("""
SELECT AVG(temperature), MIN(temperature), MAX(temperature),
       AVG(humidity), COUNT(*)
FROM readings
WHERE status = 'OK' AND timestamp >= ? AND timestamp < ?
""", (start_ts, end_ts)).fetchone()
errors = conn.execute("""
SELECT COUNT(*) FROM readings
WHERE status = 'ERROR' AND timestamp >= ? AND timestamp < ?
""", (start_ts, end_ts)).fetchone()[0]
db_total = conn.execute("SELECT COUNT(*) FROM readings").fetchone()[0]
conn.close()


def fmt(value):
    """정상 0건이면 None이므로 .1f 대신 '-' 표시"""
    return "-" if value is None else f"{value:.1f}"


def build_report(day, stats, errors):
    avg_t, min_t, max_t, avg_h, count = stats
    return f"""<!doctype html>
<html lang="ko"><meta charset="utf-8">
<title>{day} 센서 리포트</title>
<h1>{day} 센서 리포트</h1>
<ul>
  <li>평균 온도: {fmt(avg_t)} °C</li>
  <li>최저/최고: {fmt(min_t)} / {fmt(max_t)} °C</li>
  <li>평균 습도: {fmt(avg_h)} %</li>
  <li>정상 {count}건 · 오류 {errors}건</li>
</ul>
<p>기간: {start_ts} 이상 ~ {end_ts} 미만 · 생성: {datetime.now(KST).isoformat(timespec="seconds")}</p>
</html>"""


# 3) HTML 리포트 저장 (같은 날짜는 덮어씀)
REPORT_DIR.mkdir(exist_ok=True)
report_path = REPORT_DIR / f"report_{day}.html"
report_path.write_text(build_report(day, stats, errors), encoding="utf-8")
print("리포트 생성:", report_path.resolve())

# 4) CSV 내보내기
with EXPORT_PATH.open("w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["timestamp", "temperature", "humidity"])
    writer.writerows(rows)
print("CSV 내보내기:", EXPORT_PATH.resolve())

# 5) 교차 검증: 원본 CSV · DB · 리포트 · 내보내기 행 수 비교
with CSV_PATH.open("r", newline="", encoding="utf-8") as file:
    src = list(csv.DictReader(file))
csv_total = len(src)
csv_ok_today = sum(1 for r in src
                   if r["status"] == "OK" and start_ts <= r["timestamp"] < end_ts)
csv_err_today = sum(1 for r in src
                    if r["status"] == "ERROR" and start_ts <= r["timestamp"] < end_ts)
with EXPORT_PATH.open("r", newline="", encoding="utf-8") as file:
    export_rows = sum(1 for _ in csv.reader(file)) - 1   # 헤더 제외

count = stats[4]
print("\n[교차 검증]")
checks = [
    ("전체 행 수      (원본 CSV vs DB COUNT)", csv_total, db_total),
    ("오늘 정상 행 수 (원본 CSV vs 리포트)", csv_ok_today, count),
    ("오늘 정상 행 수 (리포트 vs 내보내기)", count, export_rows),
    ("오늘 오류 행 수 (원본 CSV vs 리포트)", csv_err_today, errors),
]
for name, a, b in checks:
    print(f"  {name}: {a} / {b} -> {'일치' if a == b else '불일치'}")

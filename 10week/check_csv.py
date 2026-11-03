# 10주차 1차시 확인: CSV 데이터 계약 점검
# 헤더 1개 · 시간 순서 · 열 개수 · 오류 원인 · 실패값 0 저장 여부
import csv
from datetime import datetime
from pathlib import Path

CSV_PATH = Path("environment.csv")
FIELDS = ["timestamp", "temperature", "humidity",
          "status", "device_id", "error_message"]

with CSV_PATH.open("r", newline="", encoding="utf-8") as file:
    rows = list(csv.reader(file))

header, data = rows[0], rows[1:]
problems = []

# 1) 헤더 1개
header_count = sum(1 for r in rows if r == FIELDS)
if header != FIELDS:
    problems.append(f"첫 줄이 헤더가 아님: {header}")
if header_count != 1:
    problems.append(f"헤더가 {header_count}번 나타남")

# 2) 열 개수
bad_cols = [i for i, r in enumerate(data, start=2) if len(r) != len(FIELDS)]
if bad_cols:
    problems.append(f"열 개수가 다른 줄: {bad_cols}")

# 3) 시간 순서 + 타임존
times = []
for i, r in enumerate(data, start=2):
    ts = datetime.fromisoformat(r[0])
    if ts.tzinfo is None:
        problems.append(f"{i}번째 줄 타임존 없음: {r[0]}")
    times.append(ts)
not_sorted = [i + 3 for i in range(len(times) - 1) if times[i] > times[i + 1]]
if not_sorted:
    problems.append(f"시간 역순인 줄: {not_sorted}")

# 4) 상태별 규칙
ok_rows = [r for r in data if r[3] == "OK"]
err_rows = [r for r in data if r[3] == "ERROR"]
for i, r in enumerate(data, start=2):
    if r[3] == "OK" and (r[1] == "" or r[2] == "" or r[5] != ""):
        problems.append(f"{i}번째 줄 OK인데 값이 비었거나 오류 원인이 있음")
    if r[3] == "ERROR" and (r[1] != "" or r[2] != "" or r[5] == ""):
        problems.append(f"{i}번째 줄 ERROR인데 값이 있거나 오류 원인이 없음")
    if r[3] not in ("OK", "ERROR"):
        problems.append(f"{i}번째 줄 status 값 이상: {r[3]}")

print(f"전체 레코드: {len(data)}건 (OK {len(ok_rows)} / ERROR {len(err_rows)})")
print(f"헤더 수: {header_count}")
print(f"열 개수: 모두 {len(FIELDS)}개" if not bad_cols else "열 개수: 불일치 있음")
print(f"기간: {data[0][0]} ~ {data[-1][0]}" if data else "기간: 없음")
reasons = {}
for r in err_rows:
    reasons[r[5]] = reasons.get(r[5], 0) + 1
print("오류 원인:", reasons if reasons else "없음")
print(f"30건 이상: {'통과' if len(data) >= 30 else '미달'}")
print("\n검사 결과:", "모두 통과" if not problems else "문제 발견")
for p in problems:
    print(" -", p)

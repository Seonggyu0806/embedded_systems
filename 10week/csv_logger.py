# 10주차 1차시 미션 1·2: 검증된 레코드를 CSV에 축적
# 미션 1: 5초마다 온·습도와 Asia/Seoul 시간을 기록
# 미션 2: 정상·오류를 같은 스키마로 30개 이상 저장
# 종료: COUNT회 측정 후 자동 종료, 또는 Ctrl+C
import csv
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import board
import adafruit_dht

KST = ZoneInfo("Asia/Seoul")      # 한국 표준시
DEVICE_ID = "rpi-01"              # 장치 식별자
INTERVAL = 5.0                    # 측정 주기(초)
COUNT = 36                        # 측정 횟수 (36회 x 5초 = 3분, 30개 이상)
CSV_PATH = Path("environment.csv")
FIELDS = ["timestamp", "temperature", "humidity",
          "status", "device_id", "error_message"]


def now_text():
    """타임존이 포함된 ISO 8601 문자열 (예: 2026-11-03T14:30:00+09:00)"""
    return datetime.now(KST).isoformat(timespec="seconds")


def validate(t, h):
    """값 존재 여부와 허용 범위 검사. 통과하면 소수 1자리로 반올림"""
    if t is None or h is None:
        raise ValueError("missing value")
    if not (-40.0 <= t <= 80.0):
        raise ValueError("temperature range")
    if not (0.0 <= h <= 100.0):
        raise ValueError("humidity range")
    return round(t, 1), round(h, 1)


def read_record(sensor):
    """센서를 한 번 읽어 스키마에 맞는 레코드(dict)를 만든다"""
    timestamp = now_text()
    try:
        t, h = validate(sensor.temperature, sensor.humidity)
        status, error = "OK", None
    except (RuntimeError, ValueError) as exc:
        t, h = None, None             # 실패를 0으로 저장하지 않음
        status, error = "ERROR", str(exc)
    return {
        "timestamp": timestamp,
        "temperature": t,
        "humidity": h,
        "status": status,
        "device_id": DEVICE_ID,
        "error_message": error,
    }


def ensure_csv_header():
    """파일이 처음 생성될 때만 헤더를 기록"""
    new_file = not CSV_PATH.exists()
    with CSV_PATH.open("a", newline="", encoding="utf-8") as file:
        if new_file:
            csv.writer(file).writerow(FIELDS)


def append_csv(record):
    """레코드 한 건을 헤더와 같은 열 순서로 추가 (None은 빈 칸)"""
    with CSV_PATH.open("a", newline="", encoding="utf-8") as file:
        csv.writer(file).writerow([record[f] for f in FIELDS])
        file.flush()


def main():
    ensure_csv_header()
    sensor = adafruit_dht.DHT22(board.D17, use_pulseio=False)  # DATA = GPIO17 (물리 11번)
    ok = err = 0
    print(f"측정 시작: {INTERVAL:.0f}초 간격 {COUNT}회 (Ctrl+C로 중단)")
    try:
        for n in range(1, COUNT + 1):
            started = time.monotonic()
            record = read_record(sensor)
            append_csv(record)
            if record["status"] == "OK":
                ok += 1
                print(f"{n:02d} {record['timestamp']} | OK    | "
                      f"{record['temperature']:.1f} C | {record['humidity']:.1f} %")
            else:
                err += 1
                print(f"{n:02d} {record['timestamp']} | ERROR | {record['error_message']}")
            # 측정·저장에 걸린 시간을 빼서 5초 주기를 유지
            if n < COUNT:
                time.sleep(max(0.0, INTERVAL - (time.monotonic() - started)))
    except KeyboardInterrupt:
        print("\n사용자 종료 (Ctrl+C)")
    finally:
        sensor.exit()
        print(f"\n결과: OK {ok}건 / ERROR {err}건 (총 {ok + err}건)")
        print(f"CSV: {CSV_PATH.resolve()}")


if __name__ == "__main__":
    main()

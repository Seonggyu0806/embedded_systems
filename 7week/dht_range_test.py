# 과제 3 검증 경로 시험: 온도 상한을 일부러 25℃로 낮춰 범위 초과(ValueError)를 발생시킴
import time
from datetime import datetime

import board
import adafruit_dht

COUNT = 10
INTERVAL = 2.0
T_MIN, T_MAX = -40, 25    # 시험용 (원래 80) - 실내 27℃가 범위 초과로 처리됨
H_MIN, H_MAX = 0, 100

sensor = adafruit_dht.DHT22(board.D17, use_pulseio=False)

success = read_fail = invalid = 0   # 정상 / 측정 실패 / 비정상 값

try:
    for count in range(1, COUNT + 1):
        now = datetime.now().strftime("%H:%M:%S")
        try:
            t = sensor.temperature
            h = sensor.humidity
            if t is None or h is None:
                raise ValueError("값 없음")
            if not (T_MIN <= t <= T_MAX and H_MIN <= h <= H_MAX):
                raise ValueError(f"범위 초과 (t={t}, h={h})")
            success += 1
            print(f"{count:02d} {now} | 정상   | {t:.1f} ℃ | {h:.1f} %RH")
        except RuntimeError as error:
            read_fail += 1
            print(f"{count:02d} {now} | 재시도 | {error}")
        except ValueError as error:
            invalid += 1
            print(f"{count:02d} {now} | 제외   | {error}")
        time.sleep(INTERVAL)
finally:
    sensor.exit()
    print(f"\n결과: 정상 {success}회 / 측정 실패 {read_fail}회 / 비정상 값 {invalid}회")

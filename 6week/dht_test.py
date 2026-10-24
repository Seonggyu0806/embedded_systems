import time
from datetime import datetime

import board
import adafruit_dht

COUNT = 10
INTERVAL = 2.0
T_MIN, T_MAX = -40, 80
H_MIN, H_MAX = 0, 100

sensor = adafruit_dht.DHT22(board.D17, use_pulseio=False)

success = failure = 0

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
            failure += 1
            print(f"{count:02d} {now} | 재시도 | {error}")
        except ValueError as error:
            failure += 1
            print(f"{count:02d} {now} | 제외   | {error}")
        time.sleep(INTERVAL)
finally:
    sensor.exit()
    print(f"\n결과: 성공 {success}회 / 실패 {failure}회 (총 {success + failure}회)")

# 7주차 미션 B + C: DHT22 측정값을 2초마다 OLED에 표시, 오류 화면, 경고 표시
# 실행 폴더에 font5x8.bin 이 있어야 함 / 종료는 Ctrl+C
import time
from datetime import datetime

import board
import busio
import adafruit_dht
import adafruit_ssd1306

OLED_ADDR = 0x3C          # i2cdetect -y 1 결과
INTERVAL = 2.0            # 측정 간격(초)
TEMP_WARN = 30.0          # 미션 C: 온도 30℃ 이상 경고
HUMI_WARN = 70.0          # 미션 C: 습도 70% 이상 경고

# ---- 초기화 (한 번만) ----
sensor = adafruit_dht.DHT22(board.D17, use_pulseio=False)   # DATA = GPIO17(물리 11번), I2C 핀과 별도
i2c = busio.I2C(board.SCL, board.SDA)                        # SCL=GPIO3(물리 5번), SDA=GPIO2(물리 3번)
display = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c, addr=OLED_ADDR)

ok_count = err_count = 0

try:
    while True:
        now = datetime.now().strftime("%H:%M:%S")
        try:
            # 측정 및 검증
            t = sensor.temperature
            h = sensor.humidity
            if t is None or h is None:
                raise ValueError("No value")
            if not (-40 <= t <= 80 and 0 <= h <= 100):
                raise ValueError("Out of range")

            ok_count += 1
            warn_t = t >= TEMP_WARN
            warn_h = h >= HUMI_WARN

            # 정상 화면
            display.fill(0)
            display.text(f"T: {t:.1f} C", 0, 0, 1)
            display.text(f"H: {h:.1f} %RH", 0, 12, 1)
            if warn_t or warn_h:
                display.text("!! WARNING !!", 0, 28, 1)
                if warn_t and warn_h:
                    reason = "TEMP+HUMI HIGH"
                elif warn_t:
                    reason = f"TEMP >= {TEMP_WARN:.0f}C"
                else:
                    reason = f"HUMI >= {HUMI_WARN:.0f}%"
                display.text(reason, 0, 40, 1)
                status = f"WARNING ({reason})"
            else:
                display.text("Status: OK", 0, 28, 1)
                status = "OK"
            display.text(f"OK:{ok_count} ERR:{err_count}", 0, 54, 1)
            print(f"{now} | {t:.1f} C | {h:.1f} %RH | {status}")

        except (RuntimeError, ValueError) as error:
            # 오류 화면: 이전 정상값이 남지 않도록 지우고 오류 표시
            err_count += 1
            display.fill(0)
            display.text("Sensor Error", 0, 8, 1)
            display.text(str(error)[:20], 0, 32, 1)
            display.text(f"OK:{ok_count} ERR:{err_count}", 0, 54, 1)
            print(f"{now} | Sensor Error | {error}")

        display.show()          # 정상/오류 중 준비된 화면 전송
        time.sleep(INTERVAL)

except KeyboardInterrupt:
    print("\n사용자 종료 (Ctrl+C)")
finally:
    # 정리 단계를 분리해서 OLED 정리가 실패해도 센서는 정리되게 함
    try:
        display.fill(0)
        display.show()
    except OSError as e:
        print(f"OLED 정리 실패: {e}")
    sensor.exit()
    print(f"결과: 정상 {ok_count}회 / 오류 {err_count}회")

from gpiozero import LED
from time import sleep

BLINK_ON = 0.1    # 짧게 켜진 시간
BLINK_OFF = 0.1   # 짧게 꺼진 시간
BLINK_COUNT = 3   # 빠르게 깜빡이는 횟수
REST = 1.5        # 묶음 사이 휴지 시간

led = LED(17)
try:
    cycle = 0
    while True:
        for _ in range(BLINK_COUNT):
            led.on()
            sleep(BLINK_ON)
            led.off()
            sleep(BLINK_OFF)
        sleep(REST)
        cycle += 1
        print(f"경고 패턴 {cycle}회")
except KeyboardInterrupt:
    print("\nCtrl+C 입력 → 종료합니다")
finally:
    led.off()
    led.close()
    print("LED OFF, GPIO 정리 완료")
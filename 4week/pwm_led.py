from gpiozero import PWMLED
from time import sleep

led = PWMLED(17)
try:
    # 1) 듀티비 단계별 밝기
    for value in [0.0, 0.25, 0.5, 0.75, 1.0]:
        led.value = value
        print(f"duty = {value:.2f} ({int(value * 100)}%)")
        sleep(2)

    # 2) 호흡 효과 (1초 밝아짐 + 1초 어두워짐)
    print("pulse 시작 (6초)")
    led.pulse(fade_in_time=1, fade_out_time=1)
    sleep(6)
except KeyboardInterrupt:
    print("\nCtrl+C 입력 → 종료합니다")
finally:
    led.off()
    led.close()
    print("LED OFF, GPIO 정리 완료")
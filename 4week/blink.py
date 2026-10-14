from gpiozero import LED
from time import sleep

ON_TIME = 1.0   # 켜진 시간(초)
OFF_TIME = 1.0  # 꺼진 시간(초)
REPEAT = 5      # 반복 횟수

led = LED(17)
try:
    for count in range(REPEAT):
        led.on()
        sleep(ON_TIME)
        led.off()
        sleep(OFF_TIME)
        print(f"{count + 1}회 (ON {ON_TIME}s / OFF {OFF_TIME}s)")
finally:
    led.close()
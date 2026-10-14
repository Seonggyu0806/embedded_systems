from gpiozero import LED
from time import sleep

led = LED(17)          # BCM GPIO17을 출력으로 사용
try:
    led.on()           # HIGH (3.3V)
    sleep(2)
finally:
    led.off()          # LOW (0V)
    led.close()        # GPIO 자원 반환
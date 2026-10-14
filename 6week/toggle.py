# 실습 ⑤ 토글: 누를 때마다 LED 상태 반전
from gpiozero import Button, LED  # 입력·출력 클래스
from signal import pause  # 메인 실행 흐름 대기

BOUNCE_TIME = 0.1  # 실험: 먼저 None 으로 실행해 바운스 관찰 → 0.1 로 다시 실행

# BCM 17번, 내부 풀업, 디바운스 시간
button = Button(17, bounce_time=BOUNCE_TIME)
led = LED(18)  # BCM 18번 LED 출력(초기 OFF)

press_no = 0  # 몇 번째 누름인지 기록(5회 상태표용)

def toggle_led():  # 눌릴 때마다 호출할 함수
    global press_no
    press_no += 1
    led.toggle()  # 켜짐과 꺼짐을 서로 바꿈
    state = "ON" if led.is_lit else "OFF"  # 현재 상태
    print(f"{press_no}회: LED={state}")  # 변경된 상태 출력

button.when_pressed = toggle_led  # 눌림 콜백 등록

try:
    pause()  # 프로그램을 유지하며 이벤트 처리
finally:  # 종료 시 자원 정리
    led.off()  # LED 끄기
    button.close()  # 입력 GPIO 자원 반환
    led.close()  # 출력 GPIO 자원 반환
# 실습 ⑦ 길게 누르기: 짧게/길게 누름을 다른 동작으로 
from gpiozero import Button  # 버튼 입력 클래스
from signal import pause  # 메인 실행 흐름 대기

button = Button(  # 내부 풀업을 사용하는 입력
    17,  # BCM GPIO17 사용
    bounce_time=0.1,  # 디바운스 시간 0.1초
    hold_time=2.0  # 2초 유지하면 held 이벤트
)

def pressed():  # 누름 시작에 호출(길게 눌러도 실행)
    print("짧게 누름")  # 이 문구는 짧은 누름 판정이 아님

def held():  # 2초 유지 후 추가 호출(기본 1회)
    print("2초 이상 누름")

button.when_pressed = pressed  # 누름 시작 콜백
button.when_held = held  # 길게 유지 콜백

try:
    pause()  # 프로그램을 유지하며 이벤트 처리
finally:  # 종료 시 자원 정리
    button.close()  # GPIO 자원 반환
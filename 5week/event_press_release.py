# 실습 ③-2 이벤트: 눌림과 해제를 서로 다른 함수에 연결 
from gpiozero import Button  # 버튼 입력 클래스
from signal import pause  # 메인 실행 흐름 대기

button = Button(17)  # BCM 17번, 내부 풀업 사용

def pressed():  # 누름 시작: HIGH에서 LOW로 변화
    print("PRESSED")

def released():  # 해제: LOW에서 HIGH로 변화
    print("RELEASED")

button.when_pressed = pressed  # 눌림 콜백 등록
button.when_released = released  # 해제 콜백 등록

try:
    pause()  # 프로그램을 유지하며 이벤트 처리
finally:  # 종료 시 자원 정리
    button.close()  # GPIO 자원 반환
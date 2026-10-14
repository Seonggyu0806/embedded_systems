# 실습 ① 첫 입력: 버튼이 눌릴 때까지 기다리기 
from gpiozero import Button  # 버튼 입력 클래스

button = Button(17)  # BCM 17번, 내부 풀업 사용

print("버튼을 누르세요.")  # 사용자 안내
button.wait_for_press()  # 눌림 상태가 될 때까지 대기
print("버튼이 눌렸습니다.")  # 대기 종료 후 실행

button.close()  # 사용한 GPIO 자원 반환
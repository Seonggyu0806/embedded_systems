# 실습 ⑥ 디바운싱: bounce_time 에 따른 눌림 횟수 비교 
# 방법: 버튼을 정확히 10번 누르고 마지막 count 를 기록
#       BOUNCE_TIME 을 None / 0.05 / 0.1 / 0.2 로 바꿔 반복
from gpiozero import Button  # 버튼 입력 클래스
from signal import pause  # 메인 실행 흐름 대기

BOUNCE_TIME = 0.1

button = Button(  # 입력 객체 생성
    17,  # BCM GPIO17 사용
    pull_up=True,  # 내부 풀업: 누르면 LOW
    bounce_time=BOUNCE_TIME  # 디바운스 시간
)

count = 0  # 눌림 횟수의 초기값

def count_press():  # 눌림 이벤트 처리
    global count  # 함수 밖의 count를 수정
    count += 1  # 콜백이 호출될 때 1 증가
    print(f"count={count}")  # 누적 횟수 출력

button.when_pressed = count_press  # 콜백 등록

print(f"bounce_time={BOUNCE_TIME} / 버튼을 10번 누르세요 (종료: Ctrl+C)")
try:
    pause()  # 프로그램을 유지하며 이벤트 처리
finally:  # 종료 시 자원 정리
    print(f"최종 count={count}")
    button.close()  # GPIO 자원 반환
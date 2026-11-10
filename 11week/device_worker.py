# 11주차 장치 쪽 모듈: 공유 상태 + 센서 워커 + DB 저장 워커 + LED 장치 워커
# - 센서 워커   : 5초마다 DHT22(GPIO17)를 읽어 공유 상태 갱신, 저장 Queue에 레코드 전달
# - DB 저장 워커: 저장 Queue에서 꺼내 SQLite readings 테이블에 INSERT (DB 쓰기는 이 스레드만)
# - LED 워커    : 제어 Queue에서 명령을 꺼내 GPIO27 LED에 적용 (GPIO 쓰기는 이 스레드만)
# - AUTO 모드   : 온도 >= TEMP_THRESHOLD 이면 LED ON, 아니면 OFF (명령도 같은 Queue로 보냄)
# MOCK=1 로 실행하면 센서·GPIO 없이 가짜 값으로 동작 (PC에서 API만 시험할 때)
import logging
import os
import random
import sqlite3
import threading
import time
from datetime import datetime
from queue import Empty, Full, Queue
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")
DEVICE_ID = "rpi-01"
DB_PATH = os.environ.get("DB_PATH", "sensors.db")
SENSOR_INTERVAL = 5.0                                   # DHT22 측정 주기(초)
TEMP_THRESHOLD = float(os.environ.get("TEMP_THRESHOLD", "28.0"))  # AUTO 기준 온도(℃)
WORKER_DELAY = float(os.environ.get("WORKER_DELAY", "0"))         # 느린 장치 흉내(503 시험용)
MOCK = os.environ.get("MOCK") == "1"
DHT_PIN = 17                                            # BCM GPIO17 = 물리 11번 (10주차와 동일)
LED_PIN = 27                                            # BCM GPIO27 = 물리 13번

log = logging.getLogger("device")

# ── 공유 상태 ─────────────────────────────────────────────
state_lock = threading.Lock()
system_state = {
    "temperature": None,
    "humidity": None,
    "sensor_status": "INIT",        # INIT / OK / ERROR
    "error_message": None,
    "led_state": "off",             # 실제 GPIO에 적용된 상태
    "mode": os.environ.get("START_MODE", "MANUAL"),   # AUTO / MANUAL
    "updated_at": None,             # 마지막 정상 측정 시각
    "checked_at": None,             # 마지막 측정 시도 시각
    "last_command": None,           # 마지막으로 처리한 명령 {source, state, result, at}
}

command_queue = Queue(maxsize=5)    # 제어 Queue
save_queue = Queue(maxsize=200)     # 저장 Queue
stop_event = threading.Event()


def now_text():
    return datetime.now(KST).isoformat(timespec="seconds")


def snapshot():
    with state_lock:
        return dict(system_state)


def update_state(**changes):
    with state_lock:
        system_state.update(changes)


# ── 하드웨어 추상화 ──────────────────────────────────────
class MockSensor:
    def __init__(self):
        self.t = 24.0

    def read(self):
        if random.random() < 0.1:
            raise RuntimeError("Checksum did not validate. Try again.")
        self.t += random.uniform(-0.3, 0.3)
        return round(self.t, 1), round(random.uniform(45, 55), 1)

    def exit(self):
        pass


class DhtSensor:
    def __init__(self):
        import board
        import adafruit_dht
        self.dev = adafruit_dht.DHT22(getattr(board, f"D{DHT_PIN}"), use_pulseio=False)

    def read(self):
        return self.dev.temperature, self.dev.humidity

    def exit(self):
        self.dev.exit()


class MockLed:
    def on(self):
        log.info("[MOCK] GPIO%d HIGH", LED_PIN)

    def off(self):
        log.info("[MOCK] GPIO%d LOW", LED_PIN)

    def close(self):
        pass


class BlinkaLed:
    """DHT22와 같은 Blinka(board·digitalio)로 LED 제어 → 10주차 가상환경 그대로 사용"""
    def __init__(self):
        import board
        import digitalio
        self.pin = digitalio.DigitalInOut(getattr(board, f"D{LED_PIN}"))
        self.pin.direction = digitalio.Direction.OUTPUT

    def on(self):
        self.pin.value = True

    def off(self):
        self.pin.value = False

    def close(self):
        self.pin.deinit()


def make_led():
    return MockLed() if MOCK else BlinkaLed()


def validate(t, h):
    """10주차와 같은 검증 규칙"""
    if t is None or h is None:
        raise ValueError("missing value")
    if not (-40.0 <= t <= 80.0):
        raise ValueError("temperature range")
    if not (0.0 <= h <= 100.0):
        raise ValueError("humidity range")
    return round(t, 1), round(h, 1)


# ── 센서 워커 ────────────────────────────────────────────
def sensor_worker():
    sensor = MockSensor() if MOCK else DhtSensor()
    try:
        while not stop_event.is_set():
            started = time.monotonic()
            ts = now_text()
            try:
                t, h = validate(*sensor.read())
                record = dict(timestamp=ts, temperature=t, humidity=h, status="OK",
                              device_id=DEVICE_ID, error_message=None)
                # 정상일 때만 값과 updated_at 갱신 → 화면에서 '최근 값인지' 판단 가능
                update_state(temperature=t, humidity=h, sensor_status="OK",
                             error_message=None, updated_at=ts, checked_at=ts)
            except (RuntimeError, ValueError) as exc:
                record = dict(timestamp=ts, temperature=None, humidity=None, status="ERROR",
                              device_id=DEVICE_ID, error_message=str(exc))
                # 실패 시 이전 정상값은 유지, 상태만 ERROR
                update_state(sensor_status="ERROR", error_message=str(exc), checked_at=ts)
                log.warning("sensor ERROR: %s", exc)

            try:
                save_queue.put(record, timeout=0.2)
            except Full:
                log.error("save queue full, record dropped: %s", ts)

            apply_auto_rule()
            # 측정에 걸린 시간을 빼고 대기 → 실제 주기 5초 유지
            stop_event.wait(max(0.0, SENSOR_INTERVAL - (time.monotonic() - started)))
    finally:
        sensor.exit()


def apply_auto_rule():
    """AUTO 모드에서 임계값 규칙으로 LED 결정. 바뀔 때만 명령을 보낸다"""
    s = snapshot()
    if s["mode"] != "AUTO" or s["temperature"] is None:
        return
    desired = "on" if s["temperature"] >= TEMP_THRESHOLD else "off"
    if desired != s["led_state"]:
        try:
            command_queue.put({"type": "SET_LED", "state": desired, "source": "auto",
                               "at": now_text()}, timeout=0.2)
        except Full:
            log.error("command queue full (auto)")


# ── DB 저장 워커 ─────────────────────────────────────────
CREATE_SQL = """
CREATE TABLE IF NOT EXISTS readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    temperature REAL,
    humidity REAL,
    status TEXT NOT NULL,
    device_id TEXT NOT NULL,
    error_message TEXT
)
"""
INSERT_SQL = """
INSERT INTO readings (timestamp, temperature, humidity, status, device_id, error_message)
VALUES (:timestamp, :temperature, :humidity, :status, :device_id, :error_message)
"""


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(CREATE_SQL)


def db_writer():
    conn = sqlite3.connect(DB_PATH)
    try:
        while True:
            try:
                record = save_queue.get(timeout=0.5)
            except Empty:
                if stop_event.is_set():
                    break
                continue
            if record is None:
                break
            try:
                with conn:
                    conn.execute(INSERT_SQL, record)
            except sqlite3.Error as exc:
                log.error("DB insert failed: %s", exc)
    finally:
        conn.close()


# ── LED 장치 워커 ────────────────────────────────────────
def led_worker():
    led = make_led()
    led.off()
    try:
        while True:
            try:
                cmd = command_queue.get(timeout=0.5)
            except Empty:
                if stop_event.is_set():
                    break
                continue
            if cmd is None:
                break
            if WORKER_DELAY:
                time.sleep(WORKER_DELAY)
            s = snapshot()
            # 접수 후 모드가 바뀐 경우: 출처와 현재 모드가 맞지 않으면 적용하지 않음
            allowed = (cmd["source"] == "auto") == (s["mode"] == "AUTO")
            if allowed:
                led.on() if cmd["state"] == "on" else led.off()
                result = "applied"
                update_state(led_state=cmd["state"])
            else:
                result = f"rejected (mode={s['mode']})"
            update_state(last_command={"source": cmd["source"], "state": cmd["state"],
                                       "result": result, "at": now_text()})
            log.info("LED command source=%s state=%s -> %s", cmd["source"], cmd["state"], result)
    finally:
        led.off()
        led.close()


_threads = []


def start_workers():
    init_db()
    for target, name in ((db_writer, "db-writer"), (led_worker, "led-worker"),
                         (sensor_worker, "sensor-worker")):
        th = threading.Thread(target=target, name=name, daemon=True)
        th.start()
        _threads.append(th)
    log.info("workers started (MOCK=%s, mode=%s, threshold=%.1f, DB=%s)",
             MOCK, system_state["mode"], TEMP_THRESHOLD, DB_PATH)


def stop_workers():
    stop_event.set()
    for th in _threads:
        th.join(timeout=3)
    log.info("workers stopped, LED off")

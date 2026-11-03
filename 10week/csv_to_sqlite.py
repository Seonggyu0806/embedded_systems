# 10주차 2차시 미션 A: CSV 기록과 같은 레코드를 SQLite에도 저장
# - environment.csv를 읽어 readings 테이블에 그대로 옮긴다
# - Queue로 레코드를 넘기고 DB 저장 스레드 1개가 INSERT (슬라이드 34~35쪽)
# - 다시 실행해도 중복되지 않도록 기존 행을 지우고 새로 옮긴다
import csv
import sqlite3
import threading
from pathlib import Path
from queue import Queue

CSV_PATH = Path("environment.csv")
DB_PATH = "sensors.db"
FIELDS = ["timestamp", "temperature", "humidity",
          "status", "device_id", "error_message"]

CREATE_SQL = """
CREATE TABLE IF NOT EXISTS readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,  -- 고유 번호
    timestamp TEXT NOT NULL,               -- 측정 시각
    temperature REAL,                      -- 온도 (실패 시 NULL)
    humidity REAL,                         -- 습도 (실패 시 NULL)
    status TEXT NOT NULL,                  -- OK / ERROR
    device_id TEXT NOT NULL,               -- 장치 식별자
    error_message TEXT                     -- 오류 원인
)
"""

INSERT_SQL = """
INSERT INTO readings (
    timestamp, temperature, humidity,
    status, device_id, error_message
) VALUES (?, ?, ?, ?, ?, ?)
"""


def create_table(conn):
    conn.execute(CREATE_SQL)
    conn.commit()


def insert_record(conn, record):
    """매개변수 바인딩으로 한 건 저장. 성공 시 commit, 예외 시 rollback"""
    try:
        with conn:
            conn.execute(INSERT_SQL, tuple(record[f] for f in FIELDS))
    except sqlite3.Error as exc:
        print("DB 저장 실패:", exc)
        raise


def from_csv_row(row):
    """CSV 문자열을 DB 타입으로 변환. 빈 칸은 None(NULL)"""
    return {
        "timestamp": row["timestamp"],
        "temperature": float(row["temperature"]) if row["temperature"] else None,
        "humidity": float(row["humidity"]) if row["humidity"] else None,
        "status": row["status"],
        "device_id": row["device_id"],
        "error_message": row["error_message"] or None,
    }


records = Queue(maxsize=200)      # 대기 레코드 최대 200개
saved = 0


def db_writer():
    """DB에 쓰는 유일한 스레드. None을 받으면 남은 작업 후 연결을 닫는다"""
    global saved
    conn = sqlite3.connect(DB_PATH)
    create_table(conn)
    with conn:
        conn.execute("DELETE FROM readings")   # 재실행 시 중복 방지
    try:
        while True:
            record = records.get()
            try:
                if record is None:      # 종료 신호
                    break
                insert_record(conn, record)
                saved += 1
            finally:
                records.task_done()
    finally:
        conn.close()


def main():
    writer = threading.Thread(target=db_writer, name="db-writer")
    writer.start()                  # 저장 스레드를 먼저 시작

    csv_count = 0
    try:
        with CSV_PATH.open("r", newline="", encoding="utf-8") as file:
            for row in csv.DictReader(file):    # 헤더를 키로 사용
                records.put(from_csv_row(row))
                csv_count += 1
    finally:
        records.put(None)           # 기존 레코드 뒤에 종료 신호
        writer.join()

    conn = sqlite3.connect(DB_PATH)
    db_count, ok, err = conn.execute("""
    SELECT COUNT(*), SUM(status = 'OK'), SUM(status = 'ERROR') FROM readings
    """).fetchone()
    conn.close()

    print(f"CSV 레코드: {csv_count}건")
    print(f"DB 저장   : {saved}건 (OK {ok} / ERROR {err})")
    print(f"DB COUNT  : {db_count}건 -> {'일치' if csv_count == db_count else '불일치'}")
    print(f"DB: {Path(DB_PATH).resolve()}")


if __name__ == "__main__":
    main()

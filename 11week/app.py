# 11주차 Flask 웹 서버: 상태 조회 REST API + 대시보드 + LED 원격 제어
# 실행: python app.py            (Raspberry Pi, 실제 DHT22·LED)
#       MOCK=1 python app.py     (센서·GPIO 없이 API만 시험)
# 접속: http://<Pi IP>:5000/
import logging
import sqlite3
from pathlib import Path
from queue import Full
from time import monotonic

from flask import Flask, g, jsonify, render_template, request

import device_worker as dw

Path("logs").mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("logs/server.log", encoding="utf-8")],
)
logging.getLogger("werkzeug").setLevel(logging.WARNING)   # 요청 로그는 아래에서 직접 기록
log = logging.getLogger("web")

app = Flask(__name__)


# ── 요청 로그 (슬라이드 36) ───────────────────────────────
@app.before_request
def start_timer():
    g.started = monotonic()


@app.after_request
def log_request(response):
    elapsed_ms = (monotonic() - g.started) * 1000
    log.info("%s %s %s %s %.1fms", request.remote_addr, request.method,
             request.full_path.rstrip("?"), response.status_code, elapsed_ms)
    return response


# ── 1차시: 상태 확인·조회 API ─────────────────────────────
@app.get("/health")
def health():
    return jsonify(status="ok", service="embedded-web"), 200


@app.get("/api/status")
def api_status():
    return jsonify(dw.snapshot()), 200


@app.get("/api/readings")
def api_readings():
    # 1 ~ 100 으로 제한 (음수 LIMIT은 SQLite에서 '제한 없음'이 되므로 하한도 둔다)
    limit = request.args.get("limit", 20, type=int)
    limit = max(1, min(limit, 100))
    with sqlite3.connect(dw.DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("""
            SELECT timestamp, temperature, humidity, status
            FROM readings
            ORDER BY timestamp DESC, id DESC
            LIMIT ?
        """, (limit,)).fetchall()
    return jsonify([dict(row) for row in rows]), 200


# ── 2차시: 대시보드 ──────────────────────────────────────
@app.get("/")
def dashboard():
    return render_template("index.html", threshold=dw.TEMP_THRESHOLD)


# ── 2차시: 원격 제어 API ─────────────────────────────────
@app.post("/api/led")
def api_led():
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return jsonify(error="request body must be JSON object"), 400
    state = body.get("state")
    if state not in {"on", "off"}:
        return jsonify(error="state must be on or off"), 400
    if dw.snapshot()["mode"] != "MANUAL":
        return jsonify(error="manual mode required"), 409
    command = {"type": "SET_LED", "state": state, "source": "browser", "at": dw.now_text()}
    try:
        dw.command_queue.put(command, timeout=0.2)
    except Full:
        return jsonify(error="command queue full"), 503
    return jsonify(accepted=True, command=command), 202


@app.post("/api/mode")
def api_mode():
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return jsonify(error="request body must be JSON object"), 400
    mode = body.get("mode")
    if mode not in {"AUTO", "MANUAL"}:
        return jsonify(error="mode must be AUTO or MANUAL"), 400
    dw.update_state(mode=mode)
    log.info("mode changed -> %s", mode)
    if mode == "AUTO":
        dw.apply_auto_rule()        # 전환 즉시 규칙 반영
    return jsonify(mode=mode), 200


# ── 오류도 JSON 계약으로 ─────────────────────────────────
@app.errorhandler(404)
def not_found(_):
    return jsonify(error="not found"), 404


@app.errorhandler(405)
def method_not_allowed(_):
    return jsonify(error="method not allowed"), 405


@app.errorhandler(500)
def server_error(_):
    return jsonify(error="internal server error"), 500


if __name__ == "__main__":
    dw.start_workers()
    try:
        # 같은 LAN의 다른 기기에서 접속하도록 0.0.0.0, 개발 서버이므로 debug=False
        app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
    finally:
        dw.stop_workers()

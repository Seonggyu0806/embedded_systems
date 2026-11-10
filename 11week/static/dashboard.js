// 11주차 대시보드: 2초 폴링으로 상태 갱신, 버튼으로 LED·모드 제어
const STALE_SEC = 15;   // updated_at이 15초보다 오래되면 '오래됨' 표시

const $ = (sel) => document.querySelector(sel);
let disconnected = false;   // 연결 오류 상태였는지 기억
const fmt = (v) => (v === null || v === undefined) ? "--" : Number(v).toFixed(1);

function showMessage(text, isError = false) {
  const el = $("#message");
  el.textContent = `[${new Date().toLocaleTimeString()}] ${text}`;
  el.className = isError ? "error" : "ok";
}

function setBadge(el, text, kind) {
  el.textContent = text;
  el.className = "badge " + (kind ?? "");
}

// 상태 API 조회 (슬라이드 25)
async function refreshStatus() {
  try {
    const response = await fetch("/api/status", { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    if (disconnected) {               // 끊겼다가 다시 응답을 받으면 복구 표시
      disconnected = false;
      showMessage("연결 복구");
    }

    $("#temperature").textContent = fmt(data.temperature);
    $("#humidity").textContent = fmt(data.humidity);
    setBadge($("#sensor-status"), data.sensor_status,
             data.sensor_status === "OK" ? "good" : data.sensor_status === "ERROR" ? "bad" : "");
    $("#sensor-error").textContent = data.error_message ? `(${data.error_message})` : "";
    $("#updated-at").textContent = data.updated_at ?? "--";

    if (data.updated_at) {
      const age = (Date.now() - new Date(data.updated_at).getTime()) / 1000;
      setBadge($("#freshness"), age > STALE_SEC ? `오래됨 ${Math.round(age)}s` : "최신",
               age > STALE_SEC ? "bad" : "good");
    }
    setBadge($("#led-state"), data.led_state, data.led_state === "on" ? "on" : "");
    setBadge($("#mode"), data.mode, data.mode === "AUTO" ? "auto" : "");

    const c = data.last_command;
    $("#last-command").textContent = c ? `${c.at} ${c.source} → ${c.state} (${c.result})` : "--";
    document.querySelectorAll("[data-state]").forEach(b => b.disabled = data.mode !== "MANUAL");
  } catch (error) {
    disconnected = true;
    showMessage("연결 오류: " + error.message, true);
    setBadge($("#freshness"), "연결 끊김", "bad");
  }
}

async function refreshReadings() {
  try {
    const response = await fetch("/api/readings?limit=5", { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const rows = await response.json();
    $("#readings").innerHTML = rows.map(r =>
      `<tr><td>${r.timestamp}</td><td>${fmt(r.temperature)}</td>` +
      `<td>${fmt(r.humidity)}</td><td>${r.status}</td></tr>`).join("");
  } catch (error) {
    // 상태 조회에서 이미 연결 오류를 표시하므로 여기서는 생략
  }
}

// 이전 조회가 끝난 뒤 2초 후 다음 조회 (슬라이드 26)
async function poll() {
  await refreshStatus();
  await refreshReadings();
  window.setTimeout(poll, 2000);
}

async function postJson(url, payload) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const result = await response.json();
  if (!response.ok) throw new Error(`HTTP ${response.status}: ${result.error ?? "request failed"}`);
  return result;
}

// LED 명령 (슬라이드 30): 202는 '접수'일 뿐, 실제 적용은 폴링으로 확인
async function setLed(state) {
  await postJson("/api/led", { state });
  showMessage("명령 접수: " + state);
  await refreshStatus();
}

async function setMode(mode) {
  await postJson("/api/mode", { mode });
  showMessage("모드 변경: " + mode);
  await refreshStatus();
}

document.querySelectorAll("[data-state]").forEach(button => {
  button.addEventListener("click", () =>
    setLed(button.dataset.state).catch(error => showMessage(error.message, true)));
});
document.querySelectorAll("[data-mode]").forEach(button => {
  button.addEventListener("click", () =>
    setMode(button.dataset.mode).catch(error => showMessage(error.message, true)));
});

poll();
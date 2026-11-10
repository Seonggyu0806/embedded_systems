#!/usr/bin/env bash
# 11주차 API 계약 시험 + 실행 증거 저장
# 사용: ./api_check.sh [호스트]   (기본 localhost)  예) ./api_check.sh 192.168.0.25
# 결과: evidence/api_check_<시각>.txt
HOST="${1:-localhost}"
BASE="http://${HOST}:5000"
mkdir -p evidence
OUT="evidence/api_check_$(date +%Y%m%d_%H%M%S).txt"

run() {   # run "설명" curl인자...
  echo "### $1" | tee -a "$OUT"
  shift
  echo "\$ curl $*" | tee -a "$OUT"
  curl -s -i "$@" | tr -d '\r' | grep -E '^(HTTP/|Content-Type:)|^\{|^\[' | tee -a "$OUT"
  echo | tee -a "$OUT"
}

echo "# API check $(date '+%F %T') host=$HOST" | tee "$OUT"
run "1. health"                 "$BASE/health"
run "2. status"                 "$BASE/api/status"
run "3. readings limit=5"       "$BASE/api/readings?limit=5"
run "4. readings limit=-1 (하한 보정 → 1행)" "$BASE/api/readings?limit=-1"
run "5. mode MANUAL"            -X POST -H "Content-Type: application/json" -d '{"mode":"MANUAL"}' "$BASE/api/mode"
run "6. LED on (202)"           -X POST -H "Content-Type: application/json" -d '{"state":"on"}'  "$BASE/api/led"
sleep 1
run "7. status after on"        "$BASE/api/status"
run "8. LED off (202)"          -X POST -H "Content-Type: application/json" -d '{"state":"off"}' "$BASE/api/led"
run "9. invalid state (400)"    -X POST -H "Content-Type: application/json" -d '{"state":"blink"}' "$BASE/api/led"
run "10. broken JSON (400)"     -X POST -H "Content-Type: application/json" -d '{"state":'  "$BASE/api/led"
run "11. mode AUTO"             -X POST -H "Content-Type: application/json" -d '{"mode":"AUTO"}' "$BASE/api/mode"
run "12. LED on in AUTO (409)"  -X POST -H "Content-Type: application/json" -d '{"state":"on"}'  "$BASE/api/led"
run "13. GET /api/led (405)"    "$BASE/api/led"
run "14. unknown path (404)"    "$BASE/api/nothing"
run "15. back to MANUAL"        -X POST -H "Content-Type: application/json" -d '{"mode":"MANUAL"}' "$BASE/api/mode"
echo "saved: $OUT"

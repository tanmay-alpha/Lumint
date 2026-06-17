#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────
# Lumint Live-Site End-to-End Smoke Test
# ─────────────────────────────────────────────────────────────────────
# Tests every backend endpoint the frontend uses, plus CORS preflight
# for both the production and legacy frontend origins.
#
# Usage:
#   chmod +x test_live.sh
#   ./test_live.sh
#
# First call may take 30–60s while Render's free-tier service wakes
# from sleep. Subsequent calls are <2s.
# ─────────────────────────────────────────────────────────────────────

set -u
BACKEND="https://lumint-api.onrender.com"
PROD_ORIGIN="https://lumint.vercel.app"
LEGACY_ORIGIN="https://lumint-pi.vercel.app"
PASS=0
FAIL=0

c_green="\033[0;32m"
c_red="\033[0;31m"
c_yellow="\033[1;33m"
c_reset="\033[0m"

probe() {
  local desc="$1" url="$2" expected="$3" method="${4:-GET}" data="${5:-}" origin="${6:-}"
  local headers=()
  if [ -n "$data" ]; then
    headers+=( -H "Content-Type: application/json" )
  fi
  if [ -n "$origin" ]; then
    headers+=( -H "Origin: $origin" )
  fi

  local out status
  out=$(curl -sS -m 60 -o /tmp/probe.body -w "%{http_code}" \
    -X "$method" "${headers[@]}" \
    ${data:+--data-raw "$data"} \
    "$url" 2>&1) || out="000"
  status="$out"

  if [ "$status" = "$expected" ]; then
    echo -e "  ${c_green}PASS${c_reset} [$status] $desc"
    PASS=$((PASS+1))
  else
    echo -e "  ${c_red}FAIL${c_reset} [expected $expected, got $status] $desc"
    head -c 200 /tmp/probe.body
    echo
    FAIL=$((FAIL+1))
  fi
}

probe_cors() {
  local desc="$1" url="$2" origin="$3" method="${4:-GET}"
  local out status
  out=$(curl -sS -m 60 -o /tmp/probe.body -w "%{http_code}" \
    -X OPTIONS \
    -H "Origin: $origin" \
    -H "Access-Control-Request-Method: $method" \
    "$url" 2>&1) || out="000"
  status="$out"
  if [ "$status" = "200" ] || [ "$status" = "204" ]; then
    echo -e "  ${c_green}PASS${c_reset} [$status] $desc (Origin: $origin)"
    PASS=$((PASS+1))
  else
    echo -e "  ${c_red}FAIL${c_reset} [got $status] $desc (Origin: $origin)"
    head -c 200 /tmp/probe.body
    echo
    FAIL=$((FAIL+1))
  fi
}

echo -e "${c_yellow}── Waking Render (first call may take 30-60s) ──${c_reset}"
probe "GET /health" "$BACKEND/health" 200

echo
echo -e "${c_yellow}── CORS preflight (production origin) ──${c_reset}"
probe_cors "OPTIONS /api/dashboard/stats"   "$BACKEND/api/dashboard/stats"   "$PROD_ORIGIN" GET
probe_cors "OPTIONS /api/ai/analyze-upi"    "$BACKEND/api/ai/analyze-upi"    "$PROD_ORIGIN" POST
probe_cors "OPTIONS /api/phishing/check"    "$BACKEND/api/phishing/check"    "$PROD_ORIGIN" POST
probe_cors "OPTIONS /api/upi/analyze-screenshot" "$BACKEND/api/upi/analyze-screenshot" "$PROD_ORIGIN" POST

echo
echo -e "${c_yellow}── CORS preflight (legacy origin — control) ──${c_reset}"
probe_cors "OPTIONS /api/dashboard/stats"   "$BACKEND/api/dashboard/stats"   "$LEGACY_ORIGIN" GET

echo
echo -e "${c_yellow}── Dashboard endpoints ──${c_reset}"
probe "GET /api/dashboard/stats"                  "$BACKEND/api/dashboard/stats" 200
probe "GET /api/dashboard/recent-events?limit=25" "$BACKEND/api/dashboard/recent-events?limit=25" 200
probe "GET /api/dashboard/risk-distribution"      "$BACKEND/api/dashboard/risk-distribution" 200
probe "GET /api/dashboard/indicator-summary"      "$BACKEND/api/dashboard/indicator-summary" 200

echo
echo -e "${c_yellow}── Research endpoints ──${c_reset}"
probe "GET /api/research/metrics"   "$BACKEND/api/research/metrics"   200
probe "GET /api/research/ablation"  "$BACKEND/api/research/ablation"  200
probe "GET /api/research/shap"      "$BACKEND/api/research/shap"      200
probe "GET /api/research/datasets"  "$BACKEND/api/research/datasets"  200

echo
echo -e "${c_yellow}── Fraud DNA endpoints ──${c_reset}"
probe "GET /api/fraud-dna/campaigns"     "$BACKEND/api/fraud-dna/campaigns" 200
probe "GET /api/fraud-dna/graph"         "$BACKEND/api/fraud-dna/graph"     200
probe "GET /api/fraud-dna/threat-summary" "$BACKEND/api/fraud-dna/threat-summary" 200
probe "POST /api/fraud-dna/recluster"    "$BACKEND/api/fraud-dna/recluster" 200 POST ""

echo
echo -e "${c_yellow}── PhishShield endpoints ──${c_reset}"
probe "POST /api/phishing/check" "$BACKEND/api/phishing/check" 200 POST \
  '{"url":"https://example-phishing-test.com/login"}'
probe "POST /api/ai/phishing"    "$BACKEND/api/ai/phishing"    200 POST \
  '{"url":"https://example.com","normalized_url":"https://example.com","domain":"example.com","risk_score":45,"risk_level":"SUSPICIOUS","triggered_rules":[],"domain_similarity_matches":[],"top_keywords":[],"is_official_bank_domain":false}'

echo
echo -e "${c_yellow}── DocShield endpoints ──${c_reset}"
probe "POST /api/ai/document" "$BACKEND/api/ai/document" 200 POST \
  '{"original_filename":"test.pdf","risk_score":40,"risk_level":"SUSPICIOUS","indicators":[]}'

echo
echo -e "${c_yellow}── UPI Shield endpoints (incl. new /api/ai/analyze-upi) ──${c_reset}"
probe "POST /api/ai/analyze-upi" "$BACKEND/api/ai/analyze-upi" 200 POST \
  '{"utr_number":"123456789012","risk_score":30,"sender":"a@upi","receiver":"b@upi","amount":500,"font_anomalies":false,"suspicious_handle":false}'
probe "GET /api/upi/verify-utr/123456789012" "$BACKEND/api/upi/verify-utr/123456789012" 200

echo
echo -e "${c_yellow}── Fraud DNA Campaign AI ──${c_reset}"
probe "POST /api/ai/campaign" "$BACKEND/api/ai/campaign" 200 POST \
  '{"campaign_id":"test","event_count":1,"risk_level":"LOW","avg_risk_score":10,"common_indicators":[],"common_keywords":[],"events":[]}'

echo
echo -e "${c_yellow}═══ Results ═══${c_reset}"
echo -e "  ${c_green}PASS: $PASS${c_reset}"
echo -e "  ${c_red}FAIL: $FAIL${c_reset}"

if [ "$FAIL" -gt 0 ]; then
  echo
  echo -e "${c_red}Some tests failed.${c_reset}"
  echo "Possible causes:"
  echo "  - Render deploy still in progress (check https://dashboard.render.com/)"
  echo "  - Vercel Deployment Protection is still ON (Vercel > Project > Settings > Protection)"
  exit 1
fi
echo -e "${c_green}All tests passed!${c_reset}"

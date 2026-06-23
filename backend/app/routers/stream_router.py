import asyncio
import hashlib
import random
import time
import uuid
import datetime
from fastapi import WebSocket, WebSocketDisconnect, APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.dependencies.auth import get_current_user
from app.models.models import ThreatFeedAlert, UPIShieldEvent

# Cap inbound WebSocket messages at 1KB — the threat stream is one-way
# (server -> client); the only client-sent text is a keep-alive ping.
# Limiting it here prevents a malicious client from sending arbitrarily
# large payloads to exhaust server memory or CPU.
MAX_WS_MESSAGE_BYTES = 1024

# Per-connection message rate limit (seconds between messages).
# Combined with the size cap, this prevents a single connection from
# sending 1,000 small messages per second to exhaust server CPU.
MIN_MSG_INTERVAL_S = 0.1

# Counter for periodic pruning of the rate-limit dict so it cannot grow
# without bound across long-lived processes.
_msg_counter = 0

# Per-key (api key hash prefix, or "anon") timestamp of the last received
# message. Used to enforce a minimum gap between inbound messages.
_last_msg_at: dict = {}

router = APIRouter(prefix="/ws", tags=["Streaming"], dependencies=[Depends(get_current_user)])

class ThreatStreamManager:
    """
    Manages active WebSocket connections.
    Broadcasts threat events to all connected clients.
    """
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    async def disconnect(self, ws: WebSocket):
        if ws in self.active:
            self.active.remove(ws)

    async def broadcast(self, event: dict):
        """Send threat event to all connected clients."""
        for ws in list(self.active):
            try:
                await ws.send_json(event)
            except Exception:
                if ws in self.active:
                    self.active.remove(ws)

manager = ThreatStreamManager()

@router.websocket("/threats")
async def threat_stream(websocket: WebSocket):
    """
    Client connects -> receives live threat events.
    Also replays up to last 50 threat events from DB upon connection.
    """
    await manager.connect(websocket)
    db = SessionLocal()
    try:
        events = []
        
        # 1. Fetch past ThreatFeedAlerts
        try:
            alerts = db.query(ThreatFeedAlert).order_by(ThreatFeedAlert.timestamp.desc()).limit(50).all()
            for alert in alerts:
                events.append({
                    "event_id": f"alert-{alert.id}",
                    "timestamp": alert.timestamp.isoformat() + "Z",
                    "module": "phish" if alert.indicator_type in ["domain", "ip"] else "upi",
                    "threat_level": alert.severity.upper() if alert.severity else "MEDIUM",
                    "summary": alert.description or f"Alert on {alert.value}",
                    "risk_score": 85 if alert.severity == "critical" else (65 if alert.severity == "high" else 45),
                    "ai_verdict": "PHISHING" if alert.indicator_type in ["domain", "ip"] else "FRAUD",
                    "indicators": [alert.indicator_type],
                    "drift_status": "stable"
                })
        except Exception:
            pass

        # 2. Fetch past UPIShieldEvents
        try:
            upi_events = db.query(UPIShieldEvent).order_by(UPIShieldEvent.timestamp.desc()).limit(50).all()
            for event in upi_events:
                events.append({
                    "event_id": f"upi-{event.id}",
                    "timestamp": event.timestamp.isoformat() + "Z",
                    "module": "upi",
                    "threat_level": event.risk_level.upper() if event.risk_level else "MEDIUM",
                    "summary": f"UPI screenshot verification of amount {event.amount or 0.0} INR",
                    "risk_score": event.risk_score or 50,
                    "ai_verdict": "FRAUD" if event.risk_level in ["HIGH", "CRITICAL"] else "CLEAN",
                    "indicators": ["font_anomaly"] if event.font_anomalies_detected else ["utr_check"],
                    "drift_status": "stable"
                })
        except Exception:
            pass

        # Sort combined events by timestamp (oldest first for replay progression)
        events.sort(key=lambda x: x["timestamp"])
        events = events[-50:]  # Limit to most recent 50

        # Send replayed events to the newly connected client
        for event in events:
            await websocket.send_json(event)

        # Identify the connection for rate limiting. The auth dependency
        # has already validated the user; if no api key is present, fall
        # back to "anon" so the limit still applies.
        try:
            api_key = websocket.headers.get("x-api-key") or ""
            key = hashlib.sha256(api_key.encode("utf-8")).hexdigest()[:8] if api_key else "anon"
        except Exception:
            key = "anon"

        # Loop to keep connection open. Inbound messages are keep-alive
        # pings only; we cap their size to prevent a malicious client from
        # exhausting server memory.
        global _msg_counter
        while True:
            # Read the raw event BEFORE decoding text — `receive_text()`
            # would buffer the full frame in memory first, then run the
            # size check, which defeats the cap. `receive()` returns the
            # raw bytes/text dict and lets us reject oversized frames
            # without ever decoding them.
            event = await websocket.receive()
            if event["type"] == "websocket.disconnect":
                break
            msg = event.get("text")
            if msg is None and event.get("bytes") is not None:
                # Binary frames are never expected on this channel.
                # 1003 = Unsupported Data (RFC 6455 §7.4.1).
                await websocket.close(code=1003, reason="binary not supported")
                break
            if msg is None:
                # Ping/pong or other keep-alive frame — loop again.
                continue

            # Per-connection rate limit. A single client must wait at
            # least MIN_MSG_INTERVAL_S between inbound messages;
            # otherwise we drop the connection with 1008 (Policy
            # Violation, RFC 6455 §7.4.1).
            now = time.time()
            last = _last_msg_at.get(key, 0)
            if now - last < MIN_MSG_INTERVAL_S:
                await websocket.close(code=1008, reason="message rate too high")
                break
            _last_msg_at[key] = now

            # Periodic pruning to keep the dict bounded. Every 1000
            # messages, drop entries older than 60s — these are
            # connections that have gone idle and will not return.
            _msg_counter += 1
            if _msg_counter % 1000 == 0:
                cutoff = now - 60.0
                stale = [k for k, t in _last_msg_at.items() if t < cutoff]
                for k in stale:
                    _last_msg_at.pop(k, None)

            if len(msg.encode("utf-8", errors="replace")) > MAX_WS_MESSAGE_BYTES:
                # 1009 = Message Too Big (RFC 6455 §7.4.1)
                await websocket.close(code=1009, reason="message too big")
                break

    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception:
        await manager.disconnect(websocket)
    finally:
        db.close()

@router.websocket("/threats/simulate")
async def simulate_threat_stream(
    websocket: WebSocket,
    rate: float = 1.0  # events per second
):
    """
    Demo mode: generates realistic synthetic threat events at given rate.
    Uses random_state=42 for reproducibility.
    """
    await websocket.accept()
    r = random.Random(42)
    
    phish_domains = ["paypal-security-login.com", "hdfcbank-netbanking-login.in", "sbi-kyc-verify.org", "amazon-reward-claim.net"]
    doc_files = ["invoice_2026_06_04.pdf", "salary_slip_may26.pdf", "pan_card_copy.jpg", "identity_doc.pdf"]
    upi_handles = ["paytm@ybl", "merchant@okaxis", "phonepe@oksbi", "user@upi"]
    
    try:
        while True:
            module = r.choice(["phish", "doc", "upi", "fraud_dna"])
            
            # Risk level distribution: 70% medium, 20% high, 10% critical
            roll = r.random()
            if roll < 0.70:
                threat_level = "MEDIUM"
                risk_score = r.randint(31, 60)
            elif roll < 0.90:
                threat_level = "HIGH"
                risk_score = r.randint(61, 80)
            else:
                threat_level = "CRITICAL"
                risk_score = r.randint(81, 100)
                
            # Drift status distribution: 85% stable, 10% warning, 5% drift
            drift_roll = r.random()
            if drift_roll < 0.85:
                drift_status = "stable"
            elif drift_roll < 0.95:
                drift_status = "warning"
            else:
                drift_status = "drift"

            if module == "phish":
                domain = r.choice(phish_domains)
                summary = f"Phishing URL detected targeting {domain}"
                indicators = ["suspicious TLD", "brand keyword", "homoglyph URL"]
                ai_verdict = "PHISHING"
            elif module == "doc":
                filename = r.choice(doc_files)
                summary = f"Suspicious document metadata tampering in {filename}"
                indicators = ["metadata mismatch", "modified creator tool", "invalid pdf signature"]
                ai_verdict = "TAMPERED"
            elif module == "upi":
                amount = r.randint(500, 75000)
                summary = f"UPI screenshot verification of amount {amount} INR"
                indicators = ["font anomaly", "invalid UTR format", "mismatched UPI handle"]
                ai_verdict = "FRAUD"
            else:  # fraud_dna
                summary = f"Fraud DNA Campaign Correlation Alert"
                indicators = ["shared device fingerprint", "rapid succession transactions"]
                ai_verdict = "FRAUD"

            event = {
                "event_id": str(uuid.uuid4()),
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "module": module,
                "threat_level": threat_level,
                "summary": summary,
                "risk_score": risk_score,
                "ai_verdict": ai_verdict,
                "indicators": indicators,
                "drift_status": drift_status
            }
            
            await websocket.send_json(event)
            await asyncio.sleep(1.0 / rate if rate > 0 else 1.0)
            
    except WebSocketDisconnect:
        pass
    except Exception:
        pass

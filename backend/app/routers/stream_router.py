import asyncio
import random
import uuid
import datetime
from fastapi import WebSocket, WebSocketDisconnect, APIRouter
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.models import ThreatFeedAlert, UPIShieldEvent

router = APIRouter(prefix="/ws", tags=["Streaming"])

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

        # Loop to keep connection open
        while True:
            await websocket.receive_text()
            
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
                "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
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

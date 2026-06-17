import asyncio
from fastapi import APIRouter, Depends, HTTPException, Request, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List, Set, Optional
from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.models import ThreatFeedAlert
from app.rate_limit import limiter
from app.schemas.threats import ThreatFeedCreate, ThreatFeedResponse

router = APIRouter(prefix="/api/threats", tags=["threat-feed"], dependencies=[Depends(get_current_user)])

MAX_WS_MESSAGE_BYTES = 1024

# Active WebSocket connections list
class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def broadcast(self, message: dict):
        # Broadcast message asynchronously to all active connections
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(connection)

manager = ConnectionManager()

@router.post("", response_model=ThreatFeedResponse)
@limiter.limit("30/minute")
async def create_threat_alert(request: Request, body: ThreatFeedCreate, db: Session = Depends(get_db)):
    """Create a new threat-feed alert and broadcast it to connected WebSockets.

    Rate-limited to 30/minute per client. Without this, a compromised or
    buggy client could flood the DB and the WebSocket fan-out — the
    broadcast call iterates every active connection, so it is O(N) on
    the number of connected analysts.
    """
    db_alert = ThreatFeedAlert(
        indicator_type=body.indicator_type,
        value=body.value,
        source=body.source,
        severity=body.severity,
        description=body.description,
        mitigation_strategy=body.mitigation_strategy
    )
    db.add(db_alert)
    db.commit()
    db.refresh(db_alert)

    # Broadcast new alert details to connected websockets
    alert_dict = {
        "event": "new_alert",
        "id": db_alert.id,
        "timestamp": db_alert.timestamp.isoformat(),
        "indicator_type": db_alert.indicator_type,
        "value": db_alert.value,
        "source": db_alert.source,
        "severity": db_alert.severity,
        "description": db_alert.description
    }
    await manager.broadcast(alert_dict)

    return db_alert

@router.get("", response_model=List[ThreatFeedResponse])
def list_threat_alerts(
    severity: Optional[str] = None,
    indicator_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(ThreatFeedAlert)
    if severity:
        query = query.filter(ThreatFeedAlert.severity == severity)
    if indicator_type:
        query = query.filter(ThreatFeedAlert.indicator_type == indicator_type)
        
    return query.order_by(ThreatFeedAlert.timestamp.desc()).all()

@router.websocket("/stream")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Receive the raw event dict. We use ``receive()`` (not
            # ``receive_text()``) so we can read the bytes/receive
            # structure first and reject oversized payloads BEFORE the
            # ASGI server finishes buffering them. ``receive_text()``
            # on a 1GB message would allocate the full string first;
            # the size check would then close the connection — but only
            # after the worker had already been pushed into OOM.
            #
            # In practice the threat stream is a server -> client push,
            # not client -> server, so we expect to see ``websocket.receive``
            # events of type ``websocket.disconnect`` quickly. Any text/
            # bytes frames we *do* get are treated as keepalive pings
            # and rejected if oversized.
            event = await websocket.receive()
            event_type = event.get("type")
            if event_type == "websocket.disconnect":
                break
            text = event.get("text")
            if text is not None and len(text.encode("utf-8")) > MAX_WS_MESSAGE_BYTES:
                await websocket.close(code=1009, reason="Message too large")
                break
            raw = event.get("bytes")
            if raw is not None and len(raw) > MAX_WS_MESSAGE_BYTES:
                await websocket.close(code=1009, reason="Message too large")
                break
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket)

import pytest
from fastapi.testclient import TestClient
from app.main import app
from starlette.websockets import WebSocketDisconnect

from app.routers.threats import MAX_WS_MESSAGE_BYTES, manager

def test_websocket_simulate():
    client = TestClient(app)
    with client.websocket_connect("/ws/threats/simulate?rate=10.0") as websocket:
        # Receive 3 simulated events
        for _ in range(3):
            data = websocket.receive_json()
            assert "event_id" in data
            assert "timestamp" in data
            assert "module" in data
            assert "threat_level" in data
            assert "summary" in data
            assert "risk_score" in data
            assert "ai_verdict" in data
            assert "indicators" in data
            assert "drift_status" in data
            assert data["module"] in ["phish", "doc", "upi", "fraud_dna"]

def test_websocket_replay_and_broadcast():
    client = TestClient(app)
    # Check that we can connect to live threats
    with client.websocket_connect("/ws/threats") as websocket:
        # Replays existing DB items or remains open
        # We can trigger a check to verify broadcast is received
        # (Since TestClient runs in a single-threaded/synchronous context,
        # websocket connections won't run concurrently with separate HTTP requests easily 
        # unless using asyncio or background tasks, but we can verify it opens cleanly)
        pass


def test_threat_stream_oversized_message_disconnects_manager():
    client = TestClient(app)
    manager.active_connections.clear()
    try:
        with client.websocket_connect("/api/threats/stream") as websocket:
            assert len(manager.active_connections) == 1
            websocket.send_text("x" * (MAX_WS_MESSAGE_BYTES + 1))
            with pytest.raises(WebSocketDisconnect) as exc_info:
                websocket.receive_text()
            assert exc_info.value.code == 1009

        assert len(manager.active_connections) == 0
    finally:
        manager.active_connections.clear()

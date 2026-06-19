"""Regression test for per-connection message rate limiting on
``/ws/threats`` (stream_router).

Background
----------
``MAX_WS_MESSAGE_BYTES`` (1KB) caps individual payload size, but a
single connection could still send 1,000 small messages per second to
exhaust server CPU. ``MIN_MSG_INTERVAL_S`` closes the gap by enforcing
a 100ms minimum between inbound messages — the next-too-soon message
must close the socket with RFC 6455 close code 1008 (Policy
Violation) and reason ``"message rate too high"``.
"""
import time

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.main import app
from app.routers import stream_router
from app.routers.stream_router import MIN_MSG_INTERVAL_S


@pytest.fixture(autouse=True)
def _reset_rate_limit_dict():
    """Reset the module-level rate-limit bookkeeping between tests.

    Without this, state from a previous test could mask the violation
    we're trying to detect (e.g. an entry keyed to ``"anon"`` with a
    fresh timestamp).
    """
    stream_router._last_msg_at.clear()
    stream_router._msg_counter = 0
    yield
    stream_router._last_msg_at.clear()
    stream_router._msg_counter = 0


def test_ws_rate_limit_disconnects_on_rapid_fire():
    """Two messages in <MIN_MSG_INTERVAL_S must close with code 1008.

    Sends two back-to-back text frames; the second violates the
    100ms rate gap and the server must close with code 1008 and
    reason ``"message rate too high"``.
    """
    client = TestClient(app)
    with client.websocket_connect("/ws/threats") as websocket:
        websocket.send_text("ping-1")
        websocket.send_text("ping-2")
        # Give the server time to receive both frames and call close().
        time.sleep(0.3)
        # Now actively read. The server has already closed the socket;
        # the next receive raises WebSocketDisconnect with our code.
        with pytest.raises(WebSocketDisconnect) as exc_info:
            websocket.receive_text()

    exc = exc_info.value
    assert exc.code == 1008, (
        f"expected 1008 (Policy Violation), got {exc.code}"
    )
    reason = (exc.reason or "").lower()
    assert "rate" in reason and "high" in reason, (
        f"unexpected close reason: {exc.reason!r}"
    )


def test_ws_rate_limit_allows_well_spaced_messages():
    """Messages spaced >= MIN_MSG_INTERVAL_S apart must NOT trigger
    the rate limit. We send three messages at ~150ms intervals and
    confirm the connection survives.
    """
    client = TestClient(app)
    with client.websocket_connect("/ws/threats") as websocket:
        for i in range(3):
            websocket.send_text(f"ping-{i}")
            time.sleep(MIN_MSG_INTERVAL_S + 0.05)

        # Sanity: connection still open. Close cleanly.
        websocket.close()


def test_ws_rate_limit_dict_is_periodically_pruned():
    """The dict-pruning branch must remove stale entries.

    We seed a stale entry, bump the counter so the next message
    lands on the prune branch, then send a message and assert the
    stale key is gone.
    """
    # Seed an entry that is already older than the 60s cutoff.
    stream_router._last_msg_at["stale-key"] = time.time() - 120.0
    stream_router._last_msg_at["fresh-key"] = time.time()

    # Bump the counter so the next message lands on the prune branch.
    stream_router._msg_counter = 999  # next increment hits 1000

    client = TestClient(app)
    with client.websocket_connect("/ws/threats") as websocket:
        websocket.send_text("trigger-prune")

    # After the message, pruning has run and "stale-key" must be gone
    # while "fresh-key" remains.
    assert "stale-key" not in stream_router._last_msg_at
    assert "fresh-key" in stream_router._last_msg_at

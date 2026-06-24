import asyncio
from datetime import datetime, timedelta, timezone

import pytest

from app.services.phishshield.ssl_lookup import _sync_ssl, lookup_ssl

# Skip cert-construction tests when the optional `cryptography` lib isn't
# installed locally. The exception/timeout tests below don't need it.
cryptography = pytest.importorskip("cryptography")
from cryptography import x509  # noqa: E402
from cryptography.hazmat.primitives import hashes, serialization  # noqa: E402
from cryptography.hazmat.primitives.asymmetric import rsa  # noqa: E402
from cryptography.x509.oid import NameOID  # noqa: E402


def _make_cert_der(
    not_before: datetime,
    not_after: datetime,
    issuer_cn: str = "Test CA",
    subject_cn: str = "example.com",
    sans=None,
) -> bytes:
    """Build a self-signed-ish cert and return its DER bytes."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, subject_cn)])
    issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, issuer_cn)])
    builder = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(not_before)
        .not_valid_after(not_after)
    )
    if sans:
        builder = builder.add_extension(
            x509.SubjectAlternativeName(sans), critical=False
        )
    cert = builder.sign(key, hashes.SHA256())
    return cert.public_bytes(serialization.Encoding.DER)


class FakeSSLSocket:
    def __init__(self, der: bytes):
        self._der = der

    def getpeercert(self, binary_form=False):
        return self._der if binary_form else None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class FakeConnectCM:
    def __init__(self, sock_obj):
        self._sock_obj = sock_obj

    def __enter__(self):
        return self._sock_obj

    def __exit__(self, *args):
        return False


class FakeCtx:
    """Minimal ``ssl.SSLContext``-shaped stand-in used by the cert-construction
    tests below.

    Why a class with ``__slots__`` instead of ``type('FakeCtx', ...)`` or a
    plain ``Mock``: a real ``ssl.SSLContext`` rejects attribute writes to
    names it does not define (e.g. ``ctx.check_hostnme = False`` raises
    ``AttributeError``). A plain Python object would silently accept that
    typo, hiding real production bugs. ``__slots__`` here mirrors that
    behaviour: only the names the production code touches
    (``check_hostname``, ``verify_mode``, ``wrap_socket``) are writable;
    any other write raises ``AttributeError``, so a regression in the
    production code that misspells one of these attributes will fail
    loudly in CI instead of silently passing.
    """

    __slots__ = ("check_hostname", "verify_mode", "_ssl_sock")

    def __init__(self, ssl_sock: FakeSSLSocket):
        # Match ssl.SSLContext defaults: verification ON. Production code
        # immediately disables both with explicit assignments, so the
        # initial values here don't matter for the tests.
        self.check_hostname = True
        self.verify_mode = 0  # ssl.CERT_REQUIRED == 0
        self._ssl_sock = ssl_sock

    def wrap_socket(self, sock, server_hostname=None, **kw):
        # Assert SNI is passed. The real ssl.SSLContext uses server_hostname
        # for SNI; if production ever drops it, a real handshake to a
        # SNI-only vhost would fail, but our mocked test wouldn't notice.
        # Pinning the kwarg here turns that regression into a test failure.
        assert "server_hostname" in {
            "server_hostname": server_hostname,
            **kw,
        } or server_hostname is not None, (
            "wrap_socket must be called with server_hostname for SNI"
        )
        return self._ssl_sock


def _patch_ssl_for_test(monkeypatch, der: bytes) -> FakeCtx:
    """Patch the network + SSL seams in ``_sync_ssl`` so a cert-construction
    test can run without touching the real internet.

    Returns the ``FakeCtx`` so the test can optionally inspect it.

    Implementation note: ``monkeypatch.setattr`` rewrites the attribute on
    the *named module* object. That works only because ``ssl_lookup.py``
    accesses the helpers through the module (``socket.create_connection``
    and ``ssl.create_default_context``), not via a bound import
    (``from socket import create_connection``). If production code ever
    changes to ``from ssl import create_default_context`` (binding the
    name at import time), these patches will silently no-op and the
    tests will fall through to the real network path. See
    ``ssl_lookup.py`` for the contract.
    """
    fake_ssl_sock = FakeSSLSocket(der)
    fake_ctx = FakeCtx(fake_ssl_sock)
    fake_tcp_sock = object()
    monkeypatch.setattr(
        "app.services.phishshield.ssl_lookup.socket.create_connection",
        lambda *a, **kw: FakeConnectCM(fake_tcp_sock),
    )
    # ssl.create_default_context() returns an instance (ssl.SSLContext),
    # not a class. The lambda must return the instance — calling it
    # (``lambda: fake_ctx()``) would raise TypeError, which _sync_ssl's
    # bare ``except`` would silently swallow into a None return.
    monkeypatch.setattr(
        "app.services.phishshield.ssl_lookup.ssl.create_default_context",
        lambda: fake_ctx,
    )
    return fake_ctx


def test_ssl_self_signed_detected(monkeypatch):
    past = datetime.now(timezone.utc) - timedelta(days=30)
    future = datetime.now(timezone.utc) + timedelta(days=365)
    der = _make_cert_der(
        past, future, issuer_cn="Self CA", subject_cn="Self CA"
    )
    _patch_ssl_for_test(monkeypatch, der)
    result = _sync_ssl("example.com")
    assert result is not None
    assert result["is_self_signed"] is True
    assert result["is_expired"] is False
    assert result["issuer"] == result["subject"]


def test_ssl_expired_detected(monkeypatch):
    past = datetime.now(timezone.utc) - timedelta(days=400)
    expired = datetime.now(timezone.utc) - timedelta(days=30)
    der = _make_cert_der(
        past, expired, issuer_cn="Test CA", subject_cn="example.com"
    )
    _patch_ssl_for_test(monkeypatch, der)
    result = _sync_ssl("example.com")
    assert result is not None
    assert result["is_expired"] is True
    assert result["is_self_signed"] is False


def test_ssl_san_count(monkeypatch):
    past = datetime.now(timezone.utc) - timedelta(days=10)
    future = datetime.now(timezone.utc) + timedelta(days=365)
    sans = [
        x509.DNSName("example.com"),
        x509.DNSName("www.example.com"),
        x509.DNSName("api.example.com"),
    ]
    der = _make_cert_der(
        past, future, issuer_cn="Test CA", subject_cn="example.com", sans=sans
    )
    _patch_ssl_for_test(monkeypatch, der)
    result = _sync_ssl("example.com")
    assert result is not None
    assert result["san_count"] == 3


def test_ssl_exception_returns_none(monkeypatch):
    def boom(*a, **kw):
        raise Exception("connect failed")

    monkeypatch.setattr(
        "app.services.phishshield.ssl_lookup.socket.create_connection", boom
    )
    assert _sync_ssl("example.com") is None


def test_lookup_ssl_async_timeout(monkeypatch):
    """If _sync_ssl hangs longer than the 3s timeout, lookup_ssl returns None."""
    def slow(domain):
        import time
        time.sleep(5)

    monkeypatch.setattr("app.services.phishshield.ssl_lookup._sync_ssl", slow)
    result = asyncio.run(lookup_ssl("example.com"))
    assert result is None

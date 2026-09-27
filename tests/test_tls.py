"""
Tests for TLS support in the MLLP transport.

Run: pytest tests/test_tls.py -v
"""
import datetime
import ssl

import pytest

cryptography = pytest.importorskip("cryptography")

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID


def _self_signed_cert(cert_path, key_path):
    """Write a self-signed certificate (CN/SAN = localhost) to PEM files."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "brightohir-test"),
    ])
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1))
        .not_valid_after(datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=365))
        .add_extension(x509.SubjectAlternativeName([x509.DNSName("localhost")]), critical=False)
        .sign(key, hashes.SHA256())
    )
    cert_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    key_path.write_bytes(key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.TraditionalOpenSSL,
        serialization.NoEncryption(),
    ))


MSG = "MSH|^~\\&|A|B|C|D|20260322||ADT^A01|1|P|2.5\rPID|1||999\r"


class TestTLS:
    def test_tls_roundtrip(self, tmp_path):
        from brightohir.transport import MLLPClient, MLLPServer

        cert = tmp_path / "server.crt"
        key = tmp_path / "server.key"
        _self_signed_cert(cert, key)

        def handler(message):
            assert "PID" in message
            return "MSH|^~\\&|B|A|D|C|20260322||ACK^A01|2|P|2.5\rMSA|AA|1\r"

        server = MLLPServer("127.0.0.1", 0, handler=handler, tls=True,
                            certfile=str(cert), keyfile=str(key))
        server.start_background()
        assert server.wait_started(timeout=5.0)
        port = server.port
        assert port != 0

        try:
            ctx = ssl.create_default_context(cafile=str(cert))
            with MLLPClient("127.0.0.1", port, timeout=10.0,
                            ssl_context=ctx, server_hostname="localhost") as client:
                ack = client.send(MSG)
            assert "MSA|AA" in ack
        finally:
            server.stop()

    def test_tls_server_requires_certfile(self):
        from brightohir.transport import MLLPServer
        server = MLLPServer("127.0.0.1", 0, tls=True)
        with pytest.raises(ValueError, match="certfile"):
            server._build_server_ssl_context()

    def test_plaintext_still_works(self):
        """Default (no TLS) server/client still round-trip."""
        from brightohir.transport import MLLPClient, MLLPServer

        server = MLLPServer("127.0.0.1", 0, handler=lambda m: "MSH|^~\\&|B|A|D|C|20260322||ACK|2|P|2.5\rMSA|AA|1\r")
        server.start_background()
        assert server.wait_started(timeout=5.0)
        port = server.port
        try:
            with MLLPClient("127.0.0.1", port, timeout=10.0) as client:
                ack = client.send(MSG)
            assert "MSA|AA" in ack
        finally:
            server.stop()

    def test_ssl_context_takes_precedence_over_tls_flag(self):
        """A supplied ssl_context should be used regardless of tls=False."""
        from brightohir.transport import MLLPServer
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        server = MLLPServer("127.0.0.1", 0, tls=False, ssl_context=ctx)
        assert server._ssl_context is ctx

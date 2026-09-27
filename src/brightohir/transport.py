"""
brightohir.transport
====================
MLLP (Minimal Lower Layer Protocol) transport for HL7 V2 messages, with
optional TLS encryption.

MLLP framing:
    <VT> message <FS><CR>
    VT  = 0x0B (vertical tab)
    FS  = 0x1C (file separator)
    CR  = 0x0D (carriage return)

Usage:
    # Server — receive V2 messages
    from brightohir.transport import MLLPServer

    def on_message(raw_v2: str) -> str:
        bundle = v2_to_r5(raw_v2)
        return generate_ack(raw_v2)  # ACK back

    server = MLLPServer("0.0.0.0", 2575, handler=on_message)
    server.start()  # blocking
    # or: server.start_background()  # threaded

    # Client — send V2 messages
    from brightohir.transport import MLLPClient

    client = MLLPClient("hospital.example.com", 2575)
    ack = client.send(v2_message_string)
    client.close()

TLS:
    # Server — require a certificate
    server = MLLPServer("0.0.0.0", 2575, handler=on_message,
                        tls=True, certfile="server.crt", keyfile="server.key")

    # Client — verify the server certificate (or pass a custom SSLContext)
    client = MLLPClient("hospital.example.com", 2575, tls=True)
    # For self-signed certificates in closed networks:
    client = MLLPClient("hospital.example.com", 2575,
                        ssl_context=ssl.create_default_context(cafile="ca.crt"))
"""

from __future__ import annotations

import logging
import socket
import ssl
import threading
from collections.abc import Callable

logger = logging.getLogger("brightohir.transport")

# MLLP framing bytes
MLLP_VT = b"\x0b"   # Start of message
MLLP_FS = b"\x1c"   # End of message
MLLP_CR = b"\x0d"   # Carriage return after FS


def mllp_encode(message: str) -> bytes:
    """Wrap an HL7 V2 message in MLLP framing.

    Args:
        message: Raw ER7 string

    Returns:
        MLLP-framed bytes: <VT>message<FS><CR>
    """
    return MLLP_VT + message.encode("utf-8") + MLLP_FS + MLLP_CR


def mllp_decode(data: bytes) -> str:
    """Extract HL7 V2 message from MLLP framing.

    Args:
        data: Raw bytes from TCP socket

    Returns:
        Decoded ER7 string (without MLLP frame)
    """
    msg = data
    if msg.startswith(MLLP_VT):
        msg = msg[1:]
    if msg.endswith(MLLP_CR):
        msg = msg[:-1]
    if msg.endswith(MLLP_FS):
        msg = msg[:-1]
    return msg.decode("utf-8", errors="replace")


class MLLPClient:
    """MLLP client — send V2 messages to a remote HL7 server.

    Args:
        host: Remote hostname or IP.
        port: Remote port (standard HL7 = 2575).
        timeout: Socket timeout in seconds.
        tls: If True, wrap the socket in TLS using a default (verifying)
            context. Ignored if ``ssl_context`` is provided.
        ssl_context: Pre-configured :class:`ssl.SSLContext`. When provided it
            takes precedence over ``tls`` and controls certificate verification.
        server_hostname: SNI/hostname to verify against. Defaults to ``host``
            for a default context; set to None for a custom context with
            ``check_hostname=False`` (self-signed setups).

    Example:
        client = MLLPClient("hospital.local", 2575)
        ack = client.send(adt_a01_string)
        client.close()
    """

    def __init__(
        self,
        host: str,
        port: int,
        timeout: float = 30.0,
        *,
        tls: bool = False,
        ssl_context: ssl.SSLContext | None = None,
        server_hostname: str | None = None,
    ):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.tls = tls
        self.ssl_context = ssl_context
        self.server_hostname = server_hostname
        self._sock: socket.socket | None = None

    def connect(self) -> None:
        """Establish TCP connection (wrapping in TLS when configured)."""
        raw = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        raw.settimeout(self.timeout)
        raw.connect((self.host, self.port))

        if self.tls or self.ssl_context is not None:
            ctx = self.ssl_context or ssl.create_default_context()
            hostname = self.server_hostname
            if hostname is None and self.ssl_context is None:
                hostname = self.host
            if hostname is not None:
                self._sock = ctx.wrap_socket(raw, server_hostname=hostname)
            else:
                self._sock = ctx.wrap_socket(raw)
        else:
            self._sock = raw

        logger.info(f"MLLP connected to {self.host}:{self.port} (tls={self.tls or self.ssl_context is not None})")

    def send(self, message: str) -> str:
        """Send a V2 message and wait for ACK response.

        Auto-connects if not already connected.

        Args:
            message: HL7 V2 ER7 string

        Returns:
            ACK/NAK response string
        """
        if self._sock is None:
            self.connect()

        self._sock.sendall(mllp_encode(message))
        logger.debug(f"MLLP sent {len(message)} bytes")

        # Receive response
        response = self._receive()
        logger.debug(f"MLLP received {len(response)} bytes")
        return response

    def _receive(self, buffer_size: int = 65536) -> str:
        """Receive MLLP-framed response."""
        data = b""
        while True:
            chunk = self._sock.recv(buffer_size)
            if not chunk:
                break
            data += chunk
            if MLLP_FS in data:
                break
        return mllp_decode(data)

    def close(self) -> None:
        """Close the TCP connection."""
        if self._sock:
            try:
                self._sock.close()
            except OSError:
                pass
            self._sock = None
            logger.info("MLLP connection closed")

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *exc):
        self.close()


class MLLPServer:
    """MLLP server — listen for incoming V2 messages on TCP (optionally TLS).

    Args:
        host: Bind address (e.g. "0.0.0.0").
        port: Bind port (standard HL7 = 2575). Use 0 to auto-select a free
            port; the real port is then available as ``server.port``.
        handler: Callable(raw_v2: str) → ack_string.
        max_connections: Max concurrent connections.
        timeout: Per-connection socket timeout in seconds.
        tls: If True, wrap accepted connections in TLS. Requires ``certfile``
            (and ``keyfile`` unless the key is in the cert file).
        certfile: Path to the server certificate (PEM).
        keyfile: Path to the server private key (PEM). Optional if bundled.
        ssl_context: Pre-configured :class:`ssl.SSLContext`. Takes precedence
            over ``tls``/``certfile``/``keyfile``.

    Example:
        from brightohir.transport import MLLPServer
        from brightohir import v2_to_r5
        from brightohir.ack import generate_ack

        def handle(msg: str) -> str:
            bundle = v2_to_r5(msg)
            store(bundle)  # your logic
            return generate_ack(msg, ack_code="AA")

        server = MLLPServer("0.0.0.0", 2575, handler=handle)
        server.start()  # blocking
    """

    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 2575,
        handler: Callable[[str], str] | None = None,
        max_connections: int = 10,
        timeout: float = 60.0,
        *,
        tls: bool = False,
        certfile: str | None = None,
        keyfile: str | None = None,
        ssl_context: ssl.SSLContext | None = None,
    ):
        self.host = host
        self.port = port
        self.handler = handler or self._default_handler
        self.max_connections = max_connections
        self.timeout = timeout
        self.tls = tls
        self.certfile = certfile
        self.keyfile = keyfile
        self.ssl_context = ssl_context
        self._running = False
        self._server_sock: socket.socket | None = None
        self._ssl_context: ssl.SSLContext | None = ssl_context
        self._thread: threading.Thread | None = None
        self.started = threading.Event()

    def _default_handler(self, message: str) -> str:
        """Default handler: log and ACK."""
        from .ack import generate_ack
        logger.info(f"Received V2 message ({len(message)} chars)")
        return generate_ack(message)

    def _build_server_ssl_context(self) -> ssl.SSLContext:
        """Build a TLS server context from certfile/keyfile."""
        if not self.certfile:
            raise ValueError("TLS is enabled but no certfile was provided")
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(self.certfile, self.keyfile)
        return ctx

    def start(self) -> None:
        """Start the MLLP server (blocking)."""
        self._running = True
        self.started.clear()
        self._server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_sock.bind((self.host, self.port))
        self._server_sock.listen(self.max_connections)
        self._server_sock.settimeout(1.0)  # Allow periodic check for _running
        self.port = self._server_sock.getsockname()[1]

        if self.tls or self.ssl_context is not None:
            self._ssl_context = self.ssl_context or self._build_server_ssl_context()

        self.started.set()
        logger.info(f"MLLP server listening on {self.host}:{self.port} (tls={self._ssl_context is not None})")

        while self._running:
            try:
                conn, addr = self._server_sock.accept()
                conn.settimeout(self.timeout)
                if self._ssl_context is not None:
                    try:
                        conn = self._ssl_context.wrap_socket(conn, server_side=True)
                    except ssl.SSLError:
                        logger.warning(f"TLS handshake failed from {addr}", exc_info=True)
                        conn.close()
                        continue
                t = threading.Thread(target=self._handle_connection, args=(conn, addr), daemon=True)
                t.start()
            except TimeoutError:
                continue
            except OSError:
                if self._running:
                    logger.error("MLLP server socket error", exc_info=True)
                break

    def start_background(self) -> threading.Thread:
        """Start the MLLP server in a background thread. Returns the thread."""
        self._thread = threading.Thread(target=self.start, daemon=True)
        self._thread.start()
        logger.info("MLLP server started in background thread")
        return self._thread

    def wait_started(self, timeout: float | None = 5.0) -> bool:
        """Block until the server has bound its socket and is listening."""
        return self.started.wait(timeout)

    def stop(self) -> None:
        """Stop the MLLP server."""
        self._running = False
        if self._server_sock:
            try:
                self._server_sock.close()
            except OSError:
                pass
        if self._thread:
            self._thread.join(timeout=5.0)
        self.started.clear()
        logger.info("MLLP server stopped")

    def _handle_connection(self, conn: socket.socket, addr: tuple) -> None:
        """Handle a single client connection."""
        logger.info(f"MLLP connection from {addr}")
        try:
            while self._running:
                data = self._receive_message(conn)
                if not data:
                    break
                message = mllp_decode(data)
                if not message.strip():
                    continue
                try:
                    response = self.handler(message)
                    conn.sendall(mllp_encode(response))
                except Exception:
                    logger.error(f"Handler error for {addr}", exc_info=True)
                    from .ack import generate_ack
                    nak = generate_ack(message, ack_code="AE", error_msg="Internal server error")
                    conn.sendall(mllp_encode(nak))
        except (TimeoutError, ConnectionResetError, BrokenPipeError):
            logger.debug(f"MLLP connection closed from {addr}")
        finally:
            conn.close()

    def _receive_message(self, conn: socket.socket, buffer_size: int = 65536) -> bytes:
        """Receive a complete MLLP-framed message."""
        data = b""
        while True:
            try:
                chunk = conn.recv(buffer_size)
            except TimeoutError:
                return b""
            if not chunk:
                return b""
            data += chunk
            if MLLP_FS in data:
                return data

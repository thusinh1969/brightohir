"""
brightohir.ack
==============
HL7 V2 ACK/NAK message generator.

Every V2 message received must be acknowledged with an ACK (accept) or NAK (reject).
This module generates proper MSH+MSA response segments.

ACK codes (HL7 Table 0008):
    AA = Application Accept
    AE = Application Error
    AR = Application Reject
    CA = Commit Accept (enhanced mode)
    CE = Commit Error (enhanced mode)
    CR = Commit Reject (enhanced mode)

Usage:
    from brightohir.ack import generate_ack

    # Simple ACK
    ack = generate_ack(incoming_v2_message)

    # Error NAK
    nak = generate_ack(incoming_v2_message, ack_code="AE",
                       error_msg="Patient not found", error_code="204")
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any


def generate_ack(
    original_message: str,
    *,
    ack_code: str = "AA",
    error_msg: str = "",
    error_code: str = "",
    error_severity: str = "E",
    sending_app: str = "BRIGHTOHIR",
    sending_facility: str = "",
) -> str:
    """Generate a V2 ACK/NAK response for an incoming message.

    Args:
        original_message: The raw V2 ER7 message being acknowledged
        ack_code: AA (accept), AE (error), AR (reject)
        error_msg: Human-readable error text (for AE/AR)
        error_code: Application error code
        error_severity: E (error), W (warning), I (info)
        sending_app: MSH-3 of the ACK
        sending_facility: MSH-4 of the ACK

    Returns:
        V2 ACK message string (ER7 format with \\r line terminators)
    """
    # Parse MSH from original message
    orig = _parse_msh(original_message)

    now = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    msg_ctrl_id = uuid.uuid4().hex[:10]

    # MSH: swap sender/receiver from original
    msh = (
        f"MSH|^~\\&|{sending_app}|{sending_facility}|"
        f"{orig['sending_app']}|{orig['sending_facility']}|"
        f"{now}||ACK^{orig['trigger']}^ACK|{msg_ctrl_id}|"
        f"{orig['processing_id']}|{orig['version']}"
    )

    # MSA: acknowledgment
    msa = f"MSA|{ack_code}|{orig['message_control_id']}"
    if error_msg:
        msa += f"|{error_msg}"

    segments = [msh, msa]

    # ERR segment for errors
    if ack_code in ("AE", "AR", "CE", "CR") and (error_msg or error_code):
        err = _build_err(error_code, error_msg, error_severity, orig.get("trigger", ""))
        segments.append(err)

    return "\r".join(segments) + "\r"


def generate_batch_ack(
    messages: list[str],
    *,
    results: list[dict[str, str]] | None = None,
    sending_app: str = "BRIGHTOHIR",
) -> str:
    """Generate batch ACK for multiple messages.

    Args:
        messages: List of raw V2 ER7 messages
        results: List of {"ack_code": "AA", "error_msg": ""} per message.
                 Defaults to AA for all.
        sending_app: MSH-3

    Returns:
        Batch ACK string with BHS/BTS wrapping
    """
    now = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    if results is None:
        results = [{"ack_code": "AA", "error_msg": ""}] * len(messages)

    lines = [f"BHS|^~\\&|{sending_app}|||{now}"]

    for msg, res in zip(messages, results):
        ack = generate_ack(
            msg,
            ack_code=res.get("ack_code", "AA"),
            error_msg=res.get("error_msg", ""),
            error_code=res.get("error_code", ""),
            sending_app=sending_app,
        )
        lines.append(ack.rstrip("\r"))

    lines.append(f"BTS|{len(messages)}")
    return "\r".join(lines) + "\r"


def _parse_msh(message: str) -> dict[str, str]:
    """Extract key fields from MSH segment of original message."""
    import re
    result = {
        "sending_app": "", "sending_facility": "",
        "receiving_app": "", "receiving_facility": "",
        "message_control_id": "", "processing_id": "P",
        "version": "2.5", "trigger": "A01", "message_type": "ACK",
    }

    # Normalize and get first line (MSH)
    lines = re.split(r"[\r\n]+", message.strip())
    if not lines or not lines[0].startswith("MSH"):
        return result

    fields = lines[0].split("|")
    # MSH-1 = | (field separator), MSH-2 = ^~\& (encoding chars)
    # So fields[0]="MSH", fields[1]="^~\&", fields[2]=sending_app, etc.
    if len(fields) > 2:
        result["sending_app"] = fields[2]
    if len(fields) > 3:
        result["sending_facility"] = fields[3]
    if len(fields) > 4:
        result["receiving_app"] = fields[4]
    if len(fields) > 5:
        result["receiving_facility"] = fields[5]
    if len(fields) > 8:
        msg_parts = fields[8].split("^")
        result["message_type"] = msg_parts[0] if msg_parts else "ACK"
        result["trigger"] = msg_parts[1] if len(msg_parts) > 1 else "A01"
    if len(fields) > 9:
        result["message_control_id"] = fields[9]
    if len(fields) > 10:
        result["processing_id"] = fields[10]
    if len(fields) > 11:
        result["version"] = fields[11]

    return result


def _build_err(error_code: str, error_msg: str, severity: str, trigger: str) -> str:
    """Build ERR segment."""
    # ERR|^^^error_code|severity|error_msg
    return f"ERR|^^^{error_code}|{severity}||{error_msg}"

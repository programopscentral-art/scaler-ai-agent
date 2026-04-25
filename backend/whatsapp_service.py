from twilio.rest import Client
import os
import logging

logger = logging.getLogger("scaler-agent.whatsapp")

_SID = os.getenv("TWILIO_ACCOUNT_SID")
_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
FROM = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")

_client = Client(_SID, _TOKEN) if _SID and _TOKEN else None


def format_phone(phone: str) -> str:
    """Ensure phone is in `whatsapp:+91XXXXXXXXXX` format."""
    phone = (phone or "").strip().replace(" ", "").replace("-", "")
    if phone.startswith("whatsapp:"):
        return phone
    if not phone.startswith("+"):
        phone = "+91" + phone  # default to India
    return "whatsapp:" + phone


_WA_LIMIT = 1500  # Twilio's hard limit is 1600; leave headroom for "(1/2) " prefix.


def _chunk_message(message: str, limit: int = _WA_LIMIT) -> list[str]:
    """Split a long message at paragraph boundaries so each chunk fits WhatsApp's limit."""
    if len(message) <= limit:
        return [message]

    chunks = []
    paragraphs = message.split("\n\n")
    current = ""
    for p in paragraphs:
        candidate = (current + "\n\n" + p) if current else p
        if len(candidate) <= limit:
            current = candidate
        else:
            if current:
                chunks.append(current)
            # If a single paragraph is itself too long, hard-split it.
            while len(p) > limit:
                chunks.append(p[:limit])
                p = p[limit:]
            current = p
    if current:
        chunks.append(current)

    total = len(chunks)
    return [f"({i+1}/{total}) {c}" if total > 1 else c for i, c in enumerate(chunks)]


def send_text_message(to_phone: str, message: str) -> dict:
    """Send a text WhatsApp message. Auto-splits if it exceeds the WhatsApp limit."""
    if not _client:
        logger.warning("Twilio not configured — skipping send.")
        return {"success": False, "error": "Twilio not configured", "skipped": True}

    chunks = _chunk_message(message)
    sids = []
    try:
        for chunk in chunks:
            msg = _client.messages.create(
                from_=FROM,
                to=format_phone(to_phone),
                body=chunk,
            )
            sids.append(msg.sid)
        return {"success": True, "sids": sids, "parts": len(sids)}
    except Exception as e:
        logger.exception("Twilio text send failed")
        return {"success": False, "error": str(e), "parts_sent": len(sids)}


def send_pdf_message(to_phone: str, pdf_url: str, cover_message: str) -> dict:
    """Send a WhatsApp message with PDF attachment."""
    if not _client:
        logger.warning("Twilio not configured — skipping send.")
        return {"success": False, "error": "Twilio not configured", "skipped": True}
    try:
        msg = _client.messages.create(
            from_=FROM,
            to=format_phone(to_phone),
            body=cover_message,
            media_url=[pdf_url],
        )
        return {"success": True, "sid": msg.sid}
    except Exception as e:
        logger.exception("Twilio PDF send failed")
        return {"success": False, "error": str(e)}

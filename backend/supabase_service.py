from supabase import create_client, Client
import os
import logging
from typing import Optional

logger = logging.getLogger("scaler-agent.supabase")

_URL = os.getenv("SUPABASE_URL")
_KEY = os.getenv("SUPABASE_KEY")

supabase: Optional[Client] = create_client(_URL, _KEY) if _URL and _KEY else None


def _require():
    if supabase is None:
        raise RuntimeError("Supabase is not configured (SUPABASE_URL / SUPABASE_KEY missing).")


def create_session(evaluator_phone: str, bda_phone: str) -> dict:
    _require()
    result = supabase.table("sessions").insert({
        "evaluator_phone": evaluator_phone,
        "bda_phone": bda_phone,
    }).execute()
    return result.data[0]


def create_lead(session_id: str, lead_data: dict) -> dict:
    _require()
    result = supabase.table("leads").insert({
        "session_id": session_id,
        **lead_data,
    }).execute()
    return result.data[0]


def save_nudge(lead_id: str, nudge_text: str, transcript: str = None) -> dict:
    _require()
    result = supabase.table("generated_content").insert({
        "lead_id": lead_id,
        "content_type": "nudge",
        "nudge_text": nudge_text,
        "transcript": transcript,
    }).execute()
    return result.data[0]


def save_pdf_content(
    lead_id: str,
    pdf_url: str,
    cover_message: str,
    transcript: str,
    questions: list,
) -> dict:
    _require()
    result = supabase.table("generated_content").insert({
        "lead_id": lead_id,
        "content_type": "pdf",
        "pdf_url": pdf_url,
        "cover_message": cover_message,
        "transcript": transcript,
        "extracted_questions": questions,
    }).execute()
    return result.data[0]


def update_approval(content_id: str, status: str, edited_message: str = None) -> dict:
    _require()
    update_data = {"approval_status": status}
    if edited_message:
        update_data["edited_cover_message"] = edited_message
    result = supabase.table("generated_content").update(
        update_data
    ).eq("id", content_id).execute()
    return result.data[0]


def get_content_by_id(content_id: str) -> Optional[dict]:
    _require()
    result = supabase.table("generated_content").select("*").eq(
        "id", content_id
    ).execute()
    return result.data[0] if result.data else None


def upload_pdf_to_storage(filepath: str, filename: str) -> str:
    """Upload PDF to Supabase Storage and return the public URL."""
    _require()
    with open(filepath, "rb") as f:
        try:
            supabase.storage.from_("pdfs").upload(
                filename,
                f,
                {"content-type": "application/pdf", "upsert": "true"},
            )
        except Exception as e:
            # If file already exists, try update
            logger.warning(f"Upload error (will retry as update): {e}")
            f.seek(0)
            supabase.storage.from_("pdfs").update(
                filename,
                f,
                {"content-type": "application/pdf", "upsert": "true"},
            )

    public = supabase.storage.from_("pdfs").get_public_url(filename)
    # supabase-py returns a string URL directly in newer versions
    if isinstance(public, dict):
        return public.get("publicUrl") or public.get("publicURL") or ""
    return str(public)

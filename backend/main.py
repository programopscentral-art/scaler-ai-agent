from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import os
import json
import logging
from dotenv import load_dotenv

load_dotenv()

from models import (
    LeadProfile,
    GenerateNudgeRequest,
    GeneratePDFRequest,
    ApproveRequest,
    OnboardRequest,
)
from gemini_service import (
    generate_bda_nudge,
    extract_questions_from_transcript,
    generate_pdf_content,
    transcribe_and_extract_audio,
)
from pdf_service import generate_pdf
from whatsapp_service import send_text_message, send_pdf_message
from supabase_service import (
    create_session,
    create_lead,
    save_nudge,
    save_pdf_content,
    update_approval,
    upload_pdf_to_storage,
    get_content_by_id,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("scaler-agent")

app = FastAPI(title="Scaler AI Agent", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")


@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}


@app.get("/api/sandbox-info")
async def sandbox_info():
    """Public WhatsApp sandbox details so the UI can guide users to opt in."""
    raw_from = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")
    sandbox_number = raw_from.replace("whatsapp:", "")
    join_code = os.getenv("TWILIO_SANDBOX_JOIN_CODE", "")
    twilio_configured = bool(os.getenv("TWILIO_ACCOUNT_SID") and os.getenv("TWILIO_AUTH_TOKEN"))
    return {
        "sandbox_number": sandbox_number,
        "join_code": join_code,
        "join_message": f"join {join_code}" if join_code else "",
        "twilio_configured": twilio_configured,
    }


@app.post("/api/onboard")
async def onboard(req: OnboardRequest):
    """Step 1: Evaluator sets their phone number for the session."""
    try:
        session = create_session(req.evaluator_phone, req.bda_phone)
        return {"session_id": session["id"], "status": "ready"}
    except Exception as e:
        logger.exception("Onboard failed")
        raise HTTPException(status_code=500, detail=f"Onboard failed: {e}")


@app.post("/api/register-lead")
async def register_lead(req: GenerateNudgeRequest):
    """Create a lead row without generating a nudge or sending WhatsApp.
    Used when the user jumps straight to the PDF flow without clicking 'Generate Nudge' first."""
    try:
        lead_db = create_lead(
            req.session_id,
            {
                "name": req.lead.name,
                "company": req.lead.company,
                "experience_years": req.lead.experience_years,
                "role": req.lead.role,
                "intent": req.lead.intent,
                "linkedin_summary": req.lead.linkedin_summary,
                "persona_type": req.lead.persona_type.value
                if hasattr(req.lead.persona_type, "value")
                else req.lead.persona_type,
            },
        )
        return {"lead_id": lead_db["id"]}
    except Exception as e:
        logger.exception("Lead registration failed")
        raise HTTPException(status_code=500, detail=f"Lead registration failed: {e}")


@app.post("/api/generate-nudge")
async def generate_nudge(req: GenerateNudgeRequest):
    """Generate and send BDA pre-sales nudge. No approval gate (internal message)."""
    try:
        lead_db = create_lead(
            req.session_id,
            {
                "name": req.lead.name,
                "company": req.lead.company,
                "experience_years": req.lead.experience_years,
                "role": req.lead.role,
                "intent": req.lead.intent,
                "linkedin_summary": req.lead.linkedin_summary,
                "persona_type": req.lead.persona_type.value
                if hasattr(req.lead.persona_type, "value")
                else req.lead.persona_type,
            },
        )

        nudge_text = generate_bda_nudge(req.lead)
        save_nudge(lead_db["id"], nudge_text)

        result = send_text_message(req.bda_phone, nudge_text)

        return {
            "lead_id": lead_db["id"],
            "nudge_text": nudge_text,
            "whatsapp_status": result,
        }
    except Exception as e:
        logger.exception("Nudge generation failed")
        raise HTTPException(status_code=500, detail=f"Nudge generation failed: {e}")


@app.post("/api/generate-pdf")
async def generate_pdf_endpoint(req: GeneratePDFRequest):
    """Generate personalised PDF from text transcript. Returns for BDA approval."""
    if not req.transcript or len(req.transcript.strip()) < 30:
        raise HTTPException(
            status_code=400,
            detail="Transcript required (minimum 30 characters for meaningful extraction).",
        )

    try:
        questions, summary, call_analysis = extract_questions_from_transcript(
            req.transcript, req.lead
        )

        pdf_content = generate_pdf_content(req.lead, questions, call_analysis)

        pdf_path = generate_pdf(req.lead, pdf_content)
        filename = os.path.basename(pdf_path)
        pdf_url = upload_pdf_to_storage(pdf_path, filename)

        cover_message = pdf_content.get("cover_whatsapp_message", "")

        content_db = save_pdf_content(
            req.lead_id, pdf_url, cover_message, req.transcript, questions
        )

        return {
            "content_id": content_db["id"],
            "pdf_url": pdf_url,
            "cover_message": cover_message,
            "extracted_questions": questions,
            "call_analysis": call_analysis,
        }
    except Exception as e:
        logger.exception("PDF generation failed")
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")


@app.post("/api/transcribe-audio")
async def transcribe_audio_endpoint(
    audio: UploadFile = File(...),
    lead_json: str = Form(...),
    session_id: str = Form(...),
    lead_id: str = Form(...),
):
    """Audio path: transcribe + extract questions + generate PDF in one shot."""
    try:
        lead_data = json.loads(lead_json)
        lead = LeadProfile(**lead_data)

        audio_bytes = await audio.read()
        if len(audio_bytes) > 25 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="Audio file too large (max 25MB).")

        audio_mime = audio.content_type or "audio/mp3"

        audio_result = transcribe_and_extract_audio(audio_bytes, audio_mime, lead)

        transcript = audio_result.get("transcript", "")
        questions = audio_result.get("questions", [])

        pdf_content = generate_pdf_content(lead, questions, audio_result)

        pdf_path = generate_pdf(lead, pdf_content)
        filename = os.path.basename(pdf_path)
        pdf_url = upload_pdf_to_storage(pdf_path, filename)

        cover_message = pdf_content.get("cover_whatsapp_message", "")

        content_db = save_pdf_content(
            lead_id, pdf_url, cover_message, transcript, questions
        )

        return {
            "content_id": content_db["id"],
            "transcript": transcript,
            "pdf_url": pdf_url,
            "cover_message": cover_message,
            "extracted_questions": questions,
            "call_analysis": audio_result,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Audio path failed")
        raise HTTPException(status_code=500, detail=f"Audio processing failed: {e}")


@app.post("/api/approve")
async def approve_and_send(req: ApproveRequest):
    """BDA approval gate for lead-facing PDF send."""
    try:
        if req.action == "skip":
            update_approval(req.content_id, "skipped")
            return {"status": "skipped", "message": "PDF send cancelled by BDA"}

        if req.action not in ("approve", "edit"):
            raise HTTPException(status_code=400, detail="Invalid action.")

        update_approval(
            req.content_id,
            "approved" if req.action == "approve" else "edited",
            req.edited_cover_message if req.action == "edit" else None,
        )

        content_data = get_content_by_id(req.content_id)
        if not content_data:
            raise HTTPException(status_code=404, detail="Content not found.")

        final_message = req.edited_cover_message or content_data["cover_message"]
        pdf_url = content_data["pdf_url"]

        result = send_pdf_message(req.lead_phone, pdf_url, final_message)

        return {"status": "sent", "whatsapp_result": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Approval failed")
        raise HTTPException(status_code=500, detail=f"Approval failed: {e}")


# Serve SvelteKit static build (mounted last so /api/* routes win)
_FRONTEND_BUILD = os.path.join(os.path.dirname(__file__), "..", "frontend", "build")
if os.path.isdir(_FRONTEND_BUILD):
    app.mount("/", StaticFiles(directory=_FRONTEND_BUILD, html=True), name="static")
else:
    @app.get("/")
    async def root():
        return JSONResponse(
            {
                "service": "Scaler AI Agent",
                "note": "Frontend build not found. Run `npm run build` in /frontend.",
            }
        )

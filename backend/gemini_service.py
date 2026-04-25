import google.generativeai as genai
import os
import json
import base64
from typing import List, Tuple, Dict, Any
from models import LeadProfile

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
_MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
model = genai.GenerativeModel(_MODEL_NAME)


def _strip_json_fence(text: str) -> str:
    """Gemini sometimes wraps JSON in ```json ... ``` fences. Strip them."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
        if text.endswith("```"):
            text = text[:-3].strip()
    return text


def _safe_parse_json(text: str) -> Dict[str, Any]:
    cleaned = _strip_json_fence(text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Try to find first { and last }
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1:
            return json.loads(cleaned[start : end + 1])
        raise


# ─────────────────────────────────────────────
# PROMPT 1: PRE-SALES BDA NUDGE
# ─────────────────────────────────────────────
def generate_bda_nudge(lead: LeadProfile) -> str:
    """Brief the BDA before they dial — a WhatsApp message read in under 90 seconds."""

    prompt = f"""You are a sales intelligence analyst briefing a Scaler BDA (Business Development Associate) before they call a lead. Write a WhatsApp message they will read in under 90 seconds on their phone.

LEAD DATA:
- Name: {lead.name}
- Company: {lead.company or 'Unknown'}
- Experience: {lead.experience_years if lead.experience_years is not None else 'Unknown'} years
- Current Role: {lead.role or 'Unknown'}
- Their stated intent: "{lead.intent}"
- LinkedIn summary: {lead.linkedin_summary or 'Not available'}

YOUR OUTPUT FORMAT (WhatsApp message, plain text, no markdown headings):

🎯 *{lead.name} — Quick Brief*

Who they are: [1 sentence in plain English — what their career situation actually is]

Why they're calling: [1 sentence — what's really driving this, not their surface intent]

Persona: [label like "Anxious switcher", "Skeptical expert", "Desperate fresher" — vivid and specific]

What will resonate:
• [angle 1 tied to something specific in their profile]
• [angle 2 tied to their specific situation]

Expect these objections:
• [most likely objection] → [one-line handle]
• [second likely objection] → [one-line handle]

Open with: "[Write a specific opening line they can literally say on the call — personalised to THIS person, not generic]"

⚠️ Gaps: [What we don't know about them that matters]

RULES:
- Be SPECIFIC to this exact person. No generic sales language.
- The opening line must reference something real about their profile.
- If something is inferred, say "likely" or "probably".
- Write like a colleague texting, not a corporate memo.
- HARD LIMIT: under 1400 characters TOTAL (this will be sent as a WhatsApp message). Cut adjectives before facts.
- Each bullet point: one short line, max 80 chars.
- Do NOT fabricate Scaler statistics. Use reasoning, not invented numbers."""

    response = model.generate_content(prompt)
    return response.text.strip()


# ─────────────────────────────────────────────
# PROMPT 2: EXTRACT QUESTIONS FROM TRANSCRIPT
# ─────────────────────────────────────────────
def extract_questions_from_transcript(
    transcript: str, lead: LeadProfile
) -> Tuple[List[Dict[str, Any]], str, Dict[str, Any]]:
    """Extract every specific doubt the lead raised on the call."""

    prompt = f"""You are a call quality analyst at Scaler. Extract every specific doubt, question, or objection that {lead.name} raised during this sales call.

LEAD CONTEXT:
- Name: {lead.name}
- Company: {lead.company or 'Unknown'}, {lead.experience_years if lead.experience_years is not None else '?'} years experience
- Intent: {lead.intent}

TRANSCRIPT:
{transcript}

Return ONLY valid JSON, no markdown, no preamble:
{{
  "questions": [
    {{
      "question_text": "exact words or close paraphrase of what they asked",
      "category": "one of: roi/cost, curriculum_depth, career_outcome, program_fit, personal_doubt",
      "emotional_weight": "one of: high/medium/low",
      "underlying_fear": "the real fear behind this question in one sentence"
    }}
  ],
  "lead_call_summary": "2-3 sentences: where this person is in their life right now, what they really want, what's holding them back — based on the call",
  "trust_level": "one of: high/medium/low — how much did they open up on the call",
  "recommended_tone": "one of: reassuring/aspirational/technical/empathetic — what tone will the PDF need"
}}

IMPORTANT: Only include questions/doubts that {lead.name} actually raised. Do not invent questions. If you are unsure about a specific Scaler curriculum detail, do not state it as fact."""

    response = model.generate_content(prompt)
    data = _safe_parse_json(response.text)

    questions = data.get("questions", [])
    summary = data.get("lead_call_summary", "")
    return questions, summary, data


# ─────────────────────────────────────────────
# PROMPT 3: GENERATE PDF CONTENT
# ─────────────────────────────────────────────
def generate_pdf_content(
    lead: LeadProfile, questions: list, call_analysis: dict
) -> Dict[str, Any]:
    """Compose the personal letter content for the PDF."""

    questions_formatted = "\n".join(
        [
            f"- [{q.get('category', 'general').upper()}] \"{q.get('question_text', '')}\" "
            f"(underlying fear: {q.get('underlying_fear', 'unspecified')})"
            for q in questions
        ]
    ) or "- (No explicit questions extracted — write a general reassurance addressed to the lead's intent.)"

    prompt = f"""You are writing a personalised follow-up document for {lead.name} from Scaler. This is NOT marketing material. This is a personal response to a real human being who just got off a call with specific doubts.

EVERYTHING YOU WRITE MUST BE FOR {lead.name.upper()} SPECIFICALLY.

ABOUT {lead.name}:
- Current situation: {lead.role or 'Student/professional'} at {lead.company or 'their college'}
- Experience: {lead.experience_years if lead.experience_years is not None else 0} years
- What they want: {lead.intent}
- LinkedIn: {lead.linkedin_summary or 'Not provided'}
- How they came across on the call: {call_analysis.get('lead_call_summary', '')}
- Their trust level: {call_analysis.get('trust_level', 'medium')}
- Tone needed: {call_analysis.get('recommended_tone', 'reassuring')}

THEIR EXACT QUESTIONS FROM THE CALL:
{questions_formatted}

Generate content for a 2-3 page PDF with this structure. Return ONLY valid JSON:

{{
  "headline": "A personalised headline for {lead.name} — not generic. Use their situation.",
  "opening_message": "3-4 sentences written directly to {lead.name}. Acknowledge their specific situation. Validate their doubts as reasonable. Set up that this document will address each one. Sound human, not corporate.",

  "question_answers": [
    {{
      "question": "their exact question or close paraphrase",
      "answer_headline": "a bold response headline — direct, not vague",
      "answer_body": "150-200 word answer that: (1) validates the question, (2) gives a specific concrete answer with evidence or reasoning, (3) connects to their specific situation. Do NOT use generic marketing language. Do NOT fabricate specific Scaler statistics — use reasoning and general evidence instead.",
      "evidence_note": "one concrete data point, alumni example type, or logical argument that makes this credible"
    }}
  ],

  "personalised_section": {{
    "title": "A section title specific to {lead.name}'s journey — use their actual situation",
    "body": "200-250 words. Paint a specific picture of what the next 12-18 months could look like for someone exactly like {lead.name} if they made this move. Be specific about the arc. Use concrete reasoning. No fabricated numbers.",
    "call_to_action": "A one-sentence personalised CTA for {lead.name} — why taking the entrance test is the right next move FOR THEM"
  }},

  "cover_whatsapp_message": "A short WhatsApp message (under 80 words) from the BDA to {lead.name} sharing this PDF. Sound like a person, not a template. Reference something specific from the call. Do not say 'I hope this helps' or 'please find attached'."
}}

CRITICAL RULES:
1. {lead.name}'s name must appear multiple times throughout — this is their document.
2. Every answer must reference their specific situation.
3. Do NOT fabricate Scaler statistics like '95% placement rate' — use language like 'based on Scaler's published outcomes' or 'alumni in similar profiles report'.
4. The opening message tone must match: {call_analysis.get('recommended_tone', 'reassuring')}.
5. If they asked about cost/ROI, give them actual math reasoning for their situation.
6. This PDF must read COMPLETELY differently from any other lead's PDF.
7. If you are unsure about a specific Scaler curriculum detail, say "based on publicly available information" rather than stating it as fact."""

    response = model.generate_content(prompt)
    return _safe_parse_json(response.text)


# ─────────────────────────────────────────────
# PROMPT 4: TRANSCRIBE + EXTRACT FROM AUDIO
# ─────────────────────────────────────────────
def transcribe_and_extract_audio(
    audio_bytes: bytes, audio_mime: str, lead: LeadProfile
) -> Dict[str, Any]:
    """Use Gemini's native audio understanding to transcribe + analyse in one call."""

    audio_data = base64.b64encode(audio_bytes).decode("utf-8")

    prompt = f"""You are a call analyst. Listen to this sales call recording between a Scaler BDA and a lead named {lead.name}.

Tasks:
1. Transcribe the full conversation
2. Extract every question, doubt, or objection raised by {lead.name} (the lead, NOT the BDA)
3. Summarise what you learned about {lead.name} from the call

Return ONLY valid JSON:
{{
  "transcript": "full verbatim transcript, format as 'BDA: ... \\n{lead.name}: ...'",
  "questions": [
    {{
      "question_text": "exact or close paraphrase",
      "category": "roi/cost OR curriculum_depth OR career_outcome OR program_fit OR personal_doubt",
      "emotional_weight": "high/medium/low",
      "underlying_fear": "real fear in one sentence"
    }}
  ],
  "lead_call_summary": "2-3 sentences about {lead.name}'s life situation and what they really want",
  "trust_level": "high/medium/low",
  "recommended_tone": "reassuring/aspirational/technical/empathetic"
}}"""

    response = model.generate_content(
        [
            {
                "inline_data": {
                    "mime_type": audio_mime,
                    "data": audio_data,
                }
            },
            prompt,
        ]
    )
    return _safe_parse_json(response.text)

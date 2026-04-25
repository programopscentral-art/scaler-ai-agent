from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class PersonaType(str, Enum):
    ROHAN = "rohan"
    KARTHIK = "karthik"
    MEERA = "meera"
    CUSTOM = "custom"


class LeadProfile(BaseModel):
    name: str
    company: Optional[str] = None
    experience_years: Optional[int] = None
    role: Optional[str] = None
    intent: str
    linkedin_summary: Optional[str] = None
    persona_type: PersonaType = PersonaType.CUSTOM


class GenerateNudgeRequest(BaseModel):
    lead: LeadProfile
    bda_phone: str
    session_id: str


class GeneratePDFRequest(BaseModel):
    lead: LeadProfile
    transcript: Optional[str] = None
    session_id: str
    lead_id: str


class ApproveRequest(BaseModel):
    content_id: str
    action: str = Field(..., description="approve | edit | skip")
    edited_cover_message: Optional[str] = None
    lead_phone: str


class OnboardRequest(BaseModel):
    evaluator_phone: str
    bda_phone: str


class ExtractedContent(BaseModel):
    transcript: str
    questions: List[str]
    lead_summary: str

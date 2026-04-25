from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    HRFlowable,
    Table,
    TableStyle,
)
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.pdfgen import canvas
import os
import uuid
import tempfile
from models import LeadProfile

# ── Scaler brand palette ──
SCALER_BLUE = colors.HexColor("#1B4FD8")
SCALER_DARK = colors.HexColor("#0F2A6B")
SCALER_LIGHT = colors.HexColor("#EEF2FF")
SCALER_ACCENT = colors.HexColor("#F59E0B")
TEXT_DARK = colors.HexColor("#1A1A2E")
TEXT_MID = colors.HexColor("#4B5563")
TEXT_LIGHT = colors.HexColor("#6B7280")
SUCCESS_GREEN = colors.HexColor("#059669")
WHITE = colors.white


class NumberedCanvas(canvas.Canvas):
    """Adds page numbers and footer line to every page."""

    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self._draw_footer(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def _draw_footer(self, page_count):
        self.saveState()
        self.setStrokeColor(SCALER_BLUE)
        self.setLineWidth(0.5)
        self.line(15 * mm, 15 * mm, 195 * mm, 15 * mm)
        self.setFillColor(TEXT_LIGHT)
        self.setFont("Helvetica", 8)
        self.drawCentredString(
            105 * mm,
            10 * mm,
            f"Prepared by Scaler  •  Page {self._pageNumber} of {page_count}",
        )
        self.restoreState()


def _styles():
    return {
        "h1": ParagraphStyle(
            "H1", fontName="Helvetica-Bold", fontSize=22,
            textColor=SCALER_DARK, spaceAfter=6, leading=28,
        ),
        "h2": ParagraphStyle(
            "H2", fontName="Helvetica-Bold", fontSize=14,
            textColor=SCALER_BLUE, spaceAfter=4, spaceBefore=12, leading=18,
        ),
        "body": ParagraphStyle(
            "Body", fontName="Helvetica", fontSize=10,
            textColor=TEXT_MID, spaceAfter=6, leading=16, alignment=TA_JUSTIFY,
        ),
        "caption": ParagraphStyle(
            "Caption", fontName="Helvetica-Oblique", fontSize=9,
            textColor=TEXT_LIGHT, spaceAfter=4, leading=13,
        ),
        "highlight": ParagraphStyle(
            "Highlight", fontName="Helvetica-Bold", fontSize=10,
            textColor=SCALER_BLUE, spaceAfter=4, leading=16,
        ),
        "cta": ParagraphStyle(
            "CTA", fontName="Helvetica-Bold", fontSize=12,
            textColor=WHITE, alignment=TA_CENTER, leading=18,
        ),
    }


def _safe(text) -> str:
    """Escape XML-significant chars so reportlab Paragraph doesn't break on `&` or `<`."""
    if text is None:
        return ""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def generate_pdf(lead: LeadProfile, pdf_content: dict, output_dir: str = None) -> str:
    """Generate a fully branded, personalised PDF for a lead. Returns absolute filepath."""

    output_dir = output_dir or tempfile.gettempdir()
    os.makedirs(output_dir, exist_ok=True)

    safe_name = "".join(c if c.isalnum() else "_" for c in lead.name)
    filename = f"{safe_name}_{uuid.uuid4().hex[:8]}.pdf"
    filepath = os.path.join(output_dir, filename)

    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=20 * mm,
        bottomMargin=25 * mm,
    )

    s = _styles()
    story = []

    # ── Header block ──
    header_data = [
        [
            Paragraph(
                f"For {_safe(lead.name)}",
                ParagraphStyle(
                    "HeaderName", fontName="Helvetica-Bold",
                    fontSize=26, textColor=WHITE, leading=32,
                ),
            ),
            Paragraph(
                "Prepared by Scaler",
                ParagraphStyle(
                    "HeaderSub", fontName="Helvetica", fontSize=10,
                    textColor=colors.HexColor("#93C5FD"), leading=14,
                ),
            ),
        ]
    ]
    header_table = Table(header_data, colWidths=[130 * mm, 40 * mm])
    header_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), SCALER_BLUE),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 8 * mm),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5 * mm),
            ("TOPPADDING", (0, 0), (-1, -1), 6 * mm),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6 * mm),
        ])
    )
    story.append(header_table)
    story.append(Spacer(1, 6 * mm))

    # ── Headline ──
    story.append(
        Paragraph(_safe(pdf_content.get("headline", f"Your Path Forward, {lead.name}")), s["h1"])
    )
    story.append(Spacer(1, 2 * mm))

    # ── Opening message ──
    opening_data = [[Paragraph(_safe(pdf_content.get("opening_message", "")), s["body"])]]
    opening_table = Table(opening_data, colWidths=[170 * mm])
    opening_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), SCALER_LIGHT),
            ("LEFTPADDING", (0, 0), (-1, -1), 5 * mm),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5 * mm),
            ("TOPPADDING", (0, 0), (-1, -1), 4 * mm),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4 * mm),
            ("LINEBEFORE", (0, 0), (0, 0), 2, SCALER_BLUE),
        ])
    )
    story.append(opening_table)
    story.append(Spacer(1, 6 * mm))

    # ── Q&A section ──
    story.append(Paragraph("Your Questions, Answered", s["h2"]))
    story.append(HRFlowable(width="100%", thickness=1.5, color=SCALER_BLUE))
    story.append(Spacer(1, 3 * mm))

    for i, qa in enumerate(pdf_content.get("question_answers", []), 1):
        q_data = [[
            Paragraph(
                f"Q{i}",
                ParagraphStyle(
                    "QNum", fontName="Helvetica-Bold",
                    fontSize=14, textColor=WHITE, alignment=TA_CENTER,
                ),
            ),
            Paragraph(
                f'"{_safe(qa.get("question", ""))}"',
                ParagraphStyle(
                    "QText", fontName="Helvetica-Oblique",
                    fontSize=10, textColor=TEXT_DARK, leading=15,
                ),
            ),
        ]]
        q_table = Table(q_data, colWidths=[12 * mm, 158 * mm])
        q_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (0, 0), SCALER_ACCENT),
                ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#FEF9EE")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 3 * mm),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3 * mm),
                ("TOPPADDING", (0, 0), (-1, -1), 3 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3 * mm),
            ])
        )
        story.append(q_table)
        story.append(Spacer(1, 2 * mm))

        story.append(Paragraph(_safe(qa.get("answer_headline", "")), s["highlight"]))
        story.append(Paragraph(_safe(qa.get("answer_body", "")), s["body"]))

        if qa.get("evidence_note"):
            ev_data = [[Paragraph(f"📌 {_safe(qa['evidence_note'])}", s["caption"])]]
            ev_table = Table(ev_data, colWidths=[170 * mm])
            ev_table.setStyle(
                TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F0FDF4")),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4 * mm),
                    ("TOPPADDING", (0, 0), (-1, -1), 2 * mm),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2 * mm),
                    ("LINEBEFORE", (0, 0), (0, 0), 1.5, SUCCESS_GREEN),
                ])
            )
            story.append(ev_table)

        story.append(Spacer(1, 5 * mm))

    # ── Personalised section ──
    ps = pdf_content.get("personalised_section", {})
    if ps:
        story.append(Paragraph(_safe(ps.get("title", f"Your Next Chapter, {lead.name}")), s["h2"]))
        story.append(HRFlowable(width="100%", thickness=1.5, color=SCALER_BLUE))
        story.append(Spacer(1, 3 * mm))
        story.append(Paragraph(_safe(ps.get("body", "")), s["body"]))
        story.append(Spacer(1, 6 * mm))

        cta_data = [[Paragraph(_safe(ps.get("call_to_action", "Take the Entrance Test →")), s["cta"])]]
        cta_table = Table(cta_data, colWidths=[170 * mm])
        cta_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), SCALER_BLUE),
                ("TOPPADDING", (0, 0), (-1, -1), 5 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5 * mm),
            ])
        )
        story.append(cta_table)

    story.append(Spacer(1, 8 * mm))

    # ── Footer contact ──
    footer_data = [[
        Paragraph("Questions? Reply to this message or call your BDA directly.", s["caption"]),
        Paragraph(
            "scaler.com  •  careers@scaler.com",
            ParagraphStyle(
                "FooterRight", fontName="Helvetica", fontSize=9,
                textColor=SCALER_BLUE, alignment=TA_CENTER,
            ),
        ),
    ]]
    footer_table = Table(footer_data, colWidths=[100 * mm, 70 * mm])
    footer_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), SCALER_LIGHT),
            ("TOPPADDING", (0, 0), (-1, -1), 3 * mm),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3 * mm),
            ("LEFTPADDING", (0, 0), (-1, -1), 4 * mm),
        ])
    )
    story.append(footer_table)

    doc.build(story, canvasmaker=NumberedCanvas)
    return filepath

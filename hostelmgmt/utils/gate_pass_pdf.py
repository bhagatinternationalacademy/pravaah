"""
Gate Pass PDF Generator
-----------------------
Generates a clean official hostel visitor gate pass as PDF bytes.
Uses ReportLab — pure Python, no system dependencies.

Usage:
    from hostelmgmt.utils.gate_pass_pdf import generate_gate_pass_pdf
    pdf_bytes = generate_gate_pass_pdf(visitor_instance)
"""

import io
from datetime import datetime

from reportlab.lib.pagesizes import A5
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    Table, TableStyle, HRFlowable,
)

# ── Theme colours (Navy + Emerald — matches PRAVAAH) ──────────────────────
NAVY    = colors.HexColor('#1e1b4b')
TEAL    = colors.HexColor('#0f766e')
LIGHT   = colors.HexColor('#f8fafc')
GREY    = colors.HexColor('#64748b')
DKGREY  = colors.HexColor('#1e293b')
PURPLE  = colors.HexColor('#ede9fe')
PURPBDR = colors.HexColor('#c4b5fd')
ROWALT  = colors.HexColor('#f8fafc')
DIVIDER = colors.HexColor('#e2e8f0')
WHITE   = colors.white


def _fmt_date(value):
    """Format a date/datetime/None to readable string."""
    if value is None:
        return '—'
    if isinstance(value, datetime):
        return value.strftime('%d %b %Y')
    return value.strftime('%d %b %Y')


def _fmt_time(value):
    """Extract time portion e.g. 10:30 AM."""
    if value is None:
        return '—'
    if isinstance(value, datetime):
        return value.strftime('%I:%M %p')
    return str(value)


def generate_gate_pass_pdf(visitor) -> bytes:
    """
    Generate a gate pass PDF for the given Visitor instance.

    Parameters
    ----------
    visitor : hostelmgmt.models.Visitor

    Returns
    -------
    bytes  — raw PDF ready for email attachment or HttpResponse.
    """
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A5,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
        title=f'Gate Pass — {visitor.visitor_name}',
    )

    base    = getSampleStyleSheet()['Normal']
    story   = []

    # ── Style factory ─────────────────────────────────────────────────────
    def S(name, **kw):
        return ParagraphStyle(name, parent=base, **kw)

    # Styles
    title_s   = S('T', fontSize=14, leading=17, alignment=TA_CENTER,
                  textColor=WHITE, fontName='Helvetica-Bold')
    sub_s     = S('Su', fontSize=8,  leading=10, alignment=TA_CENTER,
                  textColor=colors.HexColor('#a5b4fc'))
    badge_s   = S('Ba', fontSize=9,  leading=12, alignment=TA_CENTER,
                  textColor=NAVY, fontName='Helvetica-Bold')
    lbl_s     = S('Lb', fontSize=8,  leading=11, textColor=GREY,
                  fontName='Helvetica-Bold')
    val_s     = S('Va', fontSize=9,  leading=12, textColor=DKGREY)
    sec_s     = S('Se', fontSize=8,  leading=10, textColor=TEAL,
                  fontName='Helvetica-Bold')
    body_s    = S('Bo', fontSize=8.5, leading=13, textColor=DKGREY)
    small_s   = S('Sm', fontSize=7.5, leading=11, textColor=GREY)
    foot_s    = S('Fo', fontSize=8,  leading=11, alignment=TA_CENTER,
                  textColor=GREY, fontName='Helvetica-Oblique')
    footb_s   = S('Fb', fontSize=9,  leading=12, alignment=TA_CENTER,
                  textColor=NAVY, fontName='Helvetica-Bold')

    W = doc.width   # usable page width

    # ── 1. Header ─────────────────────────────────────────────────────────
    def _nav_table(content, style, pad_top=10, pad_bot=4):
        t = Table([[content]], colWidths=[W])
        t.setStyle(TableStyle([
            ('BACKGROUND',    (0,0), (-1,-1), NAVY),
            ('TOPPADDING',    (0,0), (-1,-1), pad_top),
            ('BOTTOMPADDING', (0,0), (-1,-1), pad_bot),
            ('LEFTPADDING',   (0,0), (-1,-1), 8),
            ('RIGHTPADDING',  (0,0), (-1,-1), 8),
        ]))
        return t

    story.append(_nav_table(
        Paragraph('HOSTEL VISITOR GATE PASS', title_s),
        title_s, pad_top=12, pad_bot=4,
    ))
    story.append(_nav_table(
        Paragraph('PRAVAAH Integrated Management Suite', sub_s),
        sub_s, pad_top=2, pad_bot=10,
    ))
    story.append(Spacer(1, 6 * mm))

    # ── 2. Gate Pass ID Badge ─────────────────────────────────────────────
    gp_id = visitor.gate_pass_id()
    badge_t = Table(
        [[Paragraph(f'Gate Pass ID :  <b>{gp_id}</b>', badge_s)]],
        colWidths=[W]
    )
    badge_t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,-1), PURPLE),
        ('TOPPADDING',    (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('BOX',           (0,0), (-1,-1), 0.5, PURPBDR),
        ('ROUNDEDCORNERS', [6]),
    ]))
    story.append(badge_t)
    story.append(Spacer(1, 5 * mm))

    # ── 3. Visitor Details ────────────────────────────────────────────────
    story.append(Paragraph('VISITOR DETAILS', sec_s))
    story.append(Spacer(1, 2 * mm))
    story.append(HRFlowable(width=W, thickness=0.5, color=TEAL))
    story.append(Spacer(1, 2 * mm))

    visit_dt = visitor.visit_date if visitor.visit_date else visitor.checkin
    rows = [
        ('Visitor Name',    visitor.visitor_name),
        ('Student Name',    visitor.student_name  or '—'),
        ('Relationship',    visitor.relationship),
        ('Visit Date',      _fmt_date(visit_dt)),
        ('Check-In Time',   _fmt_time(visitor.checkin)),
        ('Check-Out Time',  _fmt_time(visitor.checkout)),
        ('Mobile',          visitor.mobile),
    ]

    detail_data = [
        [Paragraph(lbl, lbl_s), Paragraph(str(val), val_s)]
        for lbl, val in rows
    ]

    detail_t = Table(detail_data, colWidths=[44 * mm, W - 44 * mm])
    detail_t.setStyle(TableStyle([
        ('VALIGN',        (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING',    (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING',   (1,0), (-1,-1), 6),
        ('LEFTPADDING',   (0,0), (0,-1), 0),
        ('LINEBELOW',     (0,0), (-1,-2), 0.3, DIVIDER),
        ('ROWBACKGROUNDS',(0,0), (-1,-1), [WHITE, ROWALT]),
    ]))
    story.append(detail_t)
    story.append(Spacer(1, 4 * mm))

    # ── 4. Purpose ────────────────────────────────────────────────────────
    if visitor.purpose:
        story.append(Paragraph('PURPOSE OF VISIT', sec_s))
        story.append(Spacer(1, 1.5 * mm))
        story.append(HRFlowable(width=W, thickness=0.5, color=TEAL))
        story.append(Spacer(1, 2 * mm))
        story.append(Paragraph(visitor.purpose, body_s))
        story.append(Spacer(1, 4 * mm))

    # ── 5. Instructions ───────────────────────────────────────────────────
    story.append(HRFlowable(width=W, thickness=0.8, color=NAVY))
    story.append(Spacer(1, 2 * mm))
    story.append(Paragraph('IMPORTANT INSTRUCTIONS', sec_s))
    story.append(Spacer(1, 2 * mm))

    instructions = [
        'Carry a valid government-issued photo ID (Aadhaar / PAN / Passport).',
        'This gate pass is valid only for the specified date and time.',
        'Report at the security desk and present this pass upon arrival.',
        'Visiting hours: 9:00 AM – 8:00 PM only.',
        'Follow all hostel rules and regulations during the visit.',
    ]
    for line in instructions:
        story.append(Paragraph(f'•  {line}', small_s))
        story.append(Spacer(1, 1 * mm))

    story.append(Spacer(1, 4 * mm))

    # ── 6. Approval Footer ────────────────────────────────────────────────
    story.append(HRFlowable(width=W, thickness=0.8, color=NAVY))
    story.append(Spacer(1, 3 * mm))

    foot_t = Table(
        [
            [Paragraph('Approved By', foot_s)],
            [Paragraph('Hostel Administration', footb_s)],
            [Paragraph('PRAVAAH Integrated Management Suite', foot_s)],
        ],
        colWidths=[W]
    )
    foot_t.setStyle(TableStyle([
        ('ALIGN',         (0,0), (-1,-1), 'CENTER'),
        ('TOPPADDING',    (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('BACKGROUND',    (0,0), (-1,-1), LIGHT),
        ('BOX',           (0,0), (-1,-1), 0.5, DIVIDER),
        ('ROUNDEDCORNERS', [6]),
    ]))
    story.append(foot_t)

    # ── Build PDF ─────────────────────────────────────────────────────────
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
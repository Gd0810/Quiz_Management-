import datetime
from django.utils import timezone
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table,
    TableStyle, HRFlowable, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas as rl_canvas


# ─── Color Palette (same as original) ────────────────────────────────────────
C_DEEP   = colors.HexColor('#03045e')   # deep navy
C_MID    = colors.HexColor('#0077b6')   # header blue
C_LIGHT  = colors.HexColor('#008fd1')   # accent blue
C_SKY    = colors.HexColor('#075985')   # muted blue text
C_STRIP  = colors.HexColor('#f4fdff')   # alternate row tint
C_RULE   = colors.HexColor('#e0f2fe')   # row divider
C_HEADER = colors.HexColor('#023e8a')   # header underline


# ─── Page template with header bar + footer ───────────────────────────────────
class ReportCanvas(rl_canvas.Canvas):
    """Draws a branded top bar and footer on every page."""

    def __init__(self, *args, company_name="", generated_at="", **kwargs):
        super().__init__(*args, **kwargs)
        self.company_name = company_name
        self.generated_at = generated_at
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self._draw_chrome(total)
            rl_canvas.Canvas.showPage(self)
        rl_canvas.Canvas.save(self)

    def _draw_chrome(self, total_pages):
        w, h = letter

        # ── Top accent bar (full width) ──
        self.setFillColor(C_MID)
        self.rect(0, h - 14, w, 14, fill=1, stroke=0)

        # ── Footer band ──
        self.setFillColor(C_DEEP)
        self.rect(0, 0, w, 22, fill=1, stroke=0)

        # Footer: company name left, page number right
        self.setFillColor(colors.white)
        self.setFont("Helvetica", 7.5)
        self.drawString(36, 7, self.company_name)
        page_text = f"Page {self._pageNumber} of {total_pages}"
        self.drawRightString(w - 36, 7, page_text)

        # Footer: generated date centered
        self.setFont("Helvetica", 7)
        self.setFillColor(colors.HexColor('#90e0ef'))
        self.drawCentredString(w / 2, 7, f"Generated on {self.generated_at}")


# ─── Summary stat card (3-column mini-table) ─────────────────────────────────
def _stat_cards(total, passed, failed):
    """Returns a styled 3-card summary row."""
    label_style = ParagraphStyle(
        'CardLabel', fontName='Helvetica', fontSize=8,
        textColor=colors.HexColor('#90e0ef'), leading=10, spaceAfter=2
    )
    value_style = ParagraphStyle(
        'CardValue', fontName='Helvetica-Bold', fontSize=20,
        textColor=colors.white, leading=22
    )

    def card(label, value):
        return [Paragraph(label, label_style), Paragraph(str(value), value_style)]

    cards = Table(
        [[card("TOTAL ATTEMPTS", total),
          card("PASSED  (≥ 50%)", passed),
          card("FAILED  (< 50%)", failed)]],
        colWidths=[180, 180, 180],
    )
    cards.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), C_DEEP),
        ('TOPPADDING',    (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('LEFTPADDING',   (0, 0), (-1, -1), 18),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 18),
        ('LINEAFTER',     (0, 0), (1, -1), 1, colors.HexColor('#0077b6')),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('ROUNDEDCORNERS', [6]),
    ]))
    return cards


# ─── Main export function ─────────────────────────────────────────────────────
def generate_attempts_pdf(queryset, company, response):
    """
    Generate a professional Test Attempts PDF report.

    Args:
        queryset : Attempt queryset (already filtered)
        company  : Company instance with .name
        response : Django HttpResponse (content_type set by caller)
    """
    PAGE_W = 540   # usable width: letter 612 − 36*2 margins

    current_time_str = timezone.now().strftime("%B %d, %Y  %I:%M %p")

    doc = SimpleDocTemplate(
        response,
        pagesize=letter,
        rightMargin=36, leftMargin=36,
        topMargin=50,   bottomMargin=40,
        title=f"{company.name} – Test Attempts Report",
        author=company.name,
    )

    # ── Styles ────────────────────────────────────────────────────────────────
    title_style = ParagraphStyle(
        'DocTitle', fontName='Helvetica-Bold', fontSize=22,
        leading=26, textColor=C_DEEP, spaceAfter=2
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle', fontName='Helvetica', fontSize=10,
        leading=14, textColor=C_LIGHT, spaceAfter=18
    )
    section_style = ParagraphStyle(
        'Section', fontName='Helvetica-Bold', fontSize=11,
        leading=14, textColor=C_DEEP, spaceBefore=18, spaceAfter=6
    )

    # Table paragraph styles
    th_style = ParagraphStyle(
        'TH', fontName='Helvetica-Bold', fontSize=9,
        leading=11, textColor=colors.white
    )
    name_style = ParagraphStyle(
        'CName', fontName='Helvetica-Bold', fontSize=9,
        leading=12, textColor=C_DEEP
    )
    email_style = ParagraphStyle(
        'CEmail', fontName='Helvetica', fontSize=7.5,
        leading=10, textColor=C_LIGHT
    )
    cell_style = ParagraphStyle(
        'Cell', fontName='Helvetica', fontSize=9,
        leading=12, textColor=C_SKY
    )
    bold_cell = ParagraphStyle(
        'BoldCell', fontName='Helvetica-Bold', fontSize=9,
        leading=12, textColor=C_DEEP
    )

    # ── Story ─────────────────────────────────────────────────────────────────
    story = []

    # Title block
    story.append(Paragraph(f"{company.name}", title_style))
    story.append(Paragraph("Test Attempts Report", subtitle_style))
    story.append(HRFlowable(width=PAGE_W, thickness=1.5,
                             color=C_MID, spaceAfter=16))

    # # Stat cards
    # total_count = queryset.count()
    # passed = queryset.filter(percentage__gte=50).count()
    # failed = total_count - passed
    # story.append(_stat_cards(total_count, passed, failed))
    # story.append(Spacer(1, 20))

    # Section label
    story.append(Paragraph("Attempt Details", section_style))
    story.append(HRFlowable(width=PAGE_W, thickness=0.5,
                             color=C_RULE, spaceAfter=8))

    # ── Table ─────────────────────────────────────────────────────────────────
    #  Col widths: Candidate 210 | Level 90 | Score 90 | Date 150  = 540
    col_widths = [210, 90, 90, 150]

    header_row = [
        Paragraph("CANDIDATE",     th_style),
        Paragraph("LEVEL",         th_style),
        Paragraph("SCORE",         th_style),
        Paragraph("DATE ATTEMPTED",th_style),
    ]
    data = [header_row]

    for attempt in queryset:
        # Candidate cell: name + email stacked
        candidate_cell = Table(
            [[Paragraph(attempt.candidate.name,  name_style)],
             [Paragraph(attempt.candidate.email, email_style)]],
            colWidths=[206],
        )
        candidate_cell.setStyle(TableStyle([
            ('TOPPADDING',    (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ('LEFTPADDING',   (0, 0), (-1, -1), 0),
            ('RIGHTPADDING',  (0, 0), (-1, -1), 0),
        ]))

        pct = attempt.percentage
        score_text = f"{pct}%"
        # Colour-code score: green ≥ 70, amber 50–69, red < 50
        if pct >= 70:
            score_color = colors.HexColor('#166534')
        elif pct >= 50:
            score_color = colors.HexColor('#92400e')
        else:
            score_color = colors.HexColor('#991b1b')

        score_style = ParagraphStyle(
            f'Score{pct}', fontName='Helvetica-Bold', fontSize=9,
            leading=12, textColor=score_color
        )

        local_created  = timezone.localtime(attempt.created_at)
        formatted_date = local_created.strftime("%b %d, %Y\n%I:%M %p")

        data.append([
            candidate_cell,
            Paragraph(attempt.level.capitalize(), cell_style),
            Paragraph(score_text, score_style),
            Paragraph(formatted_date, cell_style),
        ])

    table = Table(data, colWidths=col_widths, repeatRows=1)

    ts = TableStyle([
        # Header row
        ('BACKGROUND',    (0, 0), (-1, 0), C_MID),
        ('LINEBELOW',     (0, 0), (-1, 0), 2,   C_HEADER),
        ('TOPPADDING',    (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 11),
        ('LEFTPADDING',   (0, 0), (-1, 0), 10),
        ('RIGHTPADDING',  (0, 0), (-1, 0), 10),

        # Data rows
        ('VALIGN',        (0, 1), (-1, -1), 'TOP'),
        ('TOPPADDING',    (0, 1), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 9),
        ('LEFTPADDING',   (0, 1), (-1, -1), 10),
        ('RIGHTPADDING',  (0, 1), (-1, -1), 10),
        ('LINEBELOW',     (0, 1), (-1, -1), 0.5, C_RULE),
    ])

    # Alternating row tints
    for i in range(1, len(data)):
        bg = C_STRIP if i % 2 == 0 else colors.white
        ts.add('BACKGROUND', (0, i), (-1, i), bg)

    table.setStyle(ts)
    story.append(table)

    # ── Build ─────────────────────────────────────────────────────────────────
    doc.build(
        story,
        canvasmaker=lambda *a, **kw: ReportCanvas(
            *a,
            company_name=company.name,
            generated_at=current_time_str,
            **kw,
        )
    )
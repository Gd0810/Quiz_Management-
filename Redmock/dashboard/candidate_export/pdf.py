import datetime
from django.utils import timezone
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table,
    TableStyle, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas as rl_canvas

# ─── Color Palette (same as attempts list PDF) ───────────────────────────────
C_DEEP   = colors.HexColor('#03045e')   # deep navy
C_MID    = colors.HexColor('#0077b6')   # header blue
C_LIGHT  = colors.HexColor('#008fd1')   # accent blue
C_SKY    = colors.HexColor('#075985')   # muted blue text
C_STRIP  = colors.HexColor('#f4fdff')   # alternate row tint
C_RULE   = colors.HexColor('#e0f2fe')   # row divider
C_HEADER = colors.HexColor('#023e8a')   # header underline

# ─── Branded Canvas ───────────────────────────────────────────────────────────
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

        # Top accent bar
        self.setFillColor(C_MID)
        self.rect(0, h - 14, w, 14, fill=1, stroke=0)

        # Footer band
        self.setFillColor(C_DEEP)
        self.rect(0, 0, w, 22, fill=1, stroke=0)

        # Footer labels
        self.setFillColor(colors.white)
        self.setFont("Helvetica", 7.5)
        self.drawString(36, 7, self.company_name)
        page_text = f"Page {self._pageNumber} of {total_pages}"
        self.drawRightString(w - 36, 7, page_text)

        self.setFont("Helvetica", 7)
        self.setFillColor(colors.HexColor('#90e0ef'))
        self.drawCentredString(w / 2, 7, f"Generated on {self.generated_at}")


# ─── PDF Report Generator ─────────────────────────────────────────────────────
def generate_candidates_pdf(queryset, company, response):
    """
    Generate a professional Candidates PDF report.

    Args:
        queryset : Candidate queryset (already filtered)
        company  : Company instance
        response : Django HttpResponse
    """
    PAGE_W = 540   # usable width: letter 612 − 36*2 margins
    current_time_str = timezone.now().strftime("%B %d, %Y  %I:%M %p")

    doc = SimpleDocTemplate(
        response,
        pagesize=letter,
        rightMargin=36, leftMargin=36,
        topMargin=50,   bottomMargin=40,
        title=f"{company.name} – Candidates Report",
        author=company.name,
    )

    # Styles
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

    # Table text styles
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

    story = []

    # Title block
    story.append(Paragraph(f"{company.name}", title_style))
    story.append(Paragraph("Candidates Report", subtitle_style))
    story.append(HRFlowable(width=PAGE_W, thickness=1.5,
                             color=C_MID, spaceAfter=16))

    # Section label
    story.append(Paragraph("Candidate Details", section_style))
    story.append(HRFlowable(width=PAGE_W, thickness=0.5,
                             color=C_RULE, spaceAfter=8))

    # Col widths: Candidate 180 | Tech/Role 120 | Category 130 | Date 110 = 540
    col_widths = [180, 120, 130, 110]

    header_row = [
        Paragraph("CANDIDATE",        th_style),
        Paragraph("TECHNOLOGY / ROLE",th_style),
        Paragraph("LATEST CATEGORY",   th_style),
        Paragraph("DATE REGISTERED",  th_style),
    ]
    data = [header_row]

    for candidate in queryset:
        # Candidate cell: name + email stacked
        candidate_cell = Table(
            [[Paragraph(candidate.name,  name_style)],
             [Paragraph(candidate.email, email_style)]],
            colWidths=[176],
        )
        candidate_cell.setStyle(TableStyle([
            ('TOPPADDING',    (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ('LEFTPADDING',   (0, 0), (-1, -1), 0),
            ('RIGHTPADDING',  (0, 0), (-1, -1), 0),
        ]))

        designation = candidate.designation_tech or "—"
        latest_category = getattr(candidate, "latest_test_category_display", "—") or "—"

        local_created  = timezone.localtime(candidate.created_at)
        formatted_date = local_created.strftime("%b %d, %Y\n%I:%M %p")

        data.append([
            candidate_cell,
            Paragraph(designation, cell_style),
            Paragraph(latest_category, cell_style),
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

    # Build PDF doc
    doc.build(
        story,
        canvasmaker=lambda *a, **kw: ReportCanvas(
            *a,
            company_name=company.name,
            generated_at=current_time_str,
            **kw,
        )
    )

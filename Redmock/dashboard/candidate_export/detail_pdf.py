import datetime
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Flowable, HRFlowable
)
from reportlab.pdfgen import canvas as rl_canvas

# ── Palette ───────────────────────────────────────────────────────────────────
C_DEEP  = colors.HexColor('#03045e')
C_MID   = colors.HexColor('#0077b6')
C_ACC   = colors.HexColor('#0096c7')
C_LIGHT = colors.HexColor('#008fd1')
C_SKY   = colors.HexColor('#075985')
C_STRIP = colors.HexColor('#f0fdff')
C_RULE  = colors.HexColor('#e0f2fe')
C_GHOST = colors.HexColor('#e0f2fe')
C_PASS  = colors.HexColor('#059669')
C_FAIL  = colors.HexColor('#e11d48')
C_WARN  = colors.HexColor('#f59e0b')
C_SKIP  = colors.HexColor('#94a3b8')
C_WHITE = colors.white
C_PALE  = colors.HexColor('#f8feff')
C_HEADER = colors.HexColor('#023e8a')

# ── Style factory ─────────────────────────────────────────────────────────────
def _s(name, **kw):
    base = dict(fontName='Helvetica', fontSize=9, leading=13, textColor=C_SKY)
    base.update(kw)
    return ParagraphStyle(name, **base)

TITLE_S   = _s('T',  fontName='Helvetica-Bold', fontSize=22, textColor=C_DEEP, leading=26, spaceAfter=1)
SUB_S     = _s('Su', fontSize=9, textColor=C_LIGHT, spaceAfter=0)
SEC_S     = _s('Se', fontName='Helvetica-Bold', fontSize=10, textColor=C_DEEP, spaceBefore=16, spaceAfter=5)
TH_S      = _s('TH', fontName='Helvetica-Bold', fontSize=8.5, textColor=C_WHITE, leading=11)
CELL_S    = _s('C',  fontSize=8.5, leading=11)
BCELL_S   = _s('BC', fontName='Helvetica-Bold', fontSize=8.5, textColor=C_DEEP, leading=11)
LABEL_S   = _s('L',  fontSize=7.5, textColor=C_LIGHT, leading=9)
VAL_S     = _s('V',  fontName='Helvetica-Bold', fontSize=9, textColor=C_DEEP, leading=11)
CORR_S    = _s('Cr', fontName='Helvetica-Bold', fontSize=8.5, textColor=C_PASS, leading=11)
WRNG_S    = _s('Wr', fontName='Helvetica-Bold', fontSize=8.5, textColor=C_FAIL, leading=11)
PEND_S    = _s('Pd', fontName='Helvetica-Bold', fontSize=8.5, textColor=C_WARN, leading=11)


# ── Page chrome ───────────────────────────────────────────────────────────────
class _DetailCanvas(rl_canvas.Canvas):

    def __init__(self, *args, company_name='', candidate_name='',
                 generated_at='', **kwargs):
        super().__init__(*args, **kwargs)
        self.company_name   = company_name
        self.candidate_name = candidate_name
        self.generated_at   = generated_at
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

    def _draw_chrome(self, total):
        w, h = letter

        # ── Top bar ──
        self.setFillColor(C_DEEP)
        self.rect(0, h - 26, w, 26, fill=1, stroke=0)
        self.setFillColor(C_MID)
        self.rect(0, h - 26, w * 0.45, 26, fill=1, stroke=0)

        # Top bar accent
        self.setFillColor(C_ACC)
        self.rect(0, h - 26, 4, 26, fill=1, stroke=0)

        # Top-bar text
        self.setFillColor(C_WHITE)
        self.setFont('Helvetica-Bold', 8.5)
        self.drawString(12, h - 17, self.company_name.upper())
        self.setFont('Helvetica', 7.5)
        self.setFillColor(colors.HexColor('#90e0ef'))
        self.drawRightString(w - 36, h - 17,
                             f'Candidate Detail  ·  {self.candidate_name}')

        # ── Footer ──
        self.setFillColor(C_DEEP)
        self.rect(0, 0, w, 22, fill=1, stroke=0)
        self.setFillColor(colors.HexColor('#0077b6'))
        self.rect(0, 0, 4, 22, fill=1, stroke=0)

        self.setFillColor(C_WHITE)
        self.setFont('Helvetica-Bold', 7)
        self.drawString(12, 7, self.company_name)
        self.setFont('Helvetica', 7)
        self.drawRightString(w - 36, 7, f'Page {self._pageNumber} of {total}')
        self.setFillColor(colors.HexColor('#90e0ef'))
        self.setFont('Helvetica', 6.5)
        self.drawCentredString(w / 2, 7, f'Generated on {self.generated_at}')


# ── Stat card strip ───────────────────────────────────────────────────────────
class _StatCards(Flowable):
    CARD_H  = 54
    ACCENT  = 3

    def __init__(self, cards, total_width):
        super().__init__()
        self.cards       = cards   # [(label, value, accent_color), ...]
        self.total_width = total_width
        self.width       = total_width
        self.height      = self.CARD_H

    def draw(self):
        c    = self.canv
        n    = len(self.cards)
        cw   = self.total_width / n
        GAP  = 4

        for i, (label, value, accent) in enumerate(self.cards):
            x = i * cw
            w = cw - GAP

            # Card background
            c.setFillColor(C_PALE)
            c.roundRect(x, 0, w, self.CARD_H, 4, fill=1, stroke=0)

            # Accent border top
            c.setFillColor(accent)
            c.roundRect(x, self.CARD_H - self.ACCENT, w,
                        self.ACCENT, 2, fill=1, stroke=0)

            # Label
            c.setFillColor(C_LIGHT)
            c.setFont('Helvetica', 6.5)
            c.drawString(x + 10, self.CARD_H - 14, label.upper())

            # Value
            val_str = str(value)
            font_sz = 14 if len(val_str) <= 6 else 11
            c.setFillColor(C_DEEP)
            c.setFont('Helvetica-Bold', font_sz)
            c.drawString(x + 10, 12, val_str)

            if i < n - 1:
                c.setStrokeColor(C_RULE)
                c.setLineWidth(0.5)
                c.line(x + w + GAP / 2, 6, x + w + GAP / 2, self.CARD_H - 6)


# ── Section header ────────────────────────────────────────────────────────────
class _SectionHeader(Flowable):
    H = 20

    def __init__(self, title, width):
        super().__init__()
        self.title = title
        self.width = width
        self.height = self.H

    def draw(self):
        c = self.canv
        c.setFillColor(C_STRIP)
        c.roundRect(0, 0, self.width, self.H, 3, fill=1, stroke=0)
        c.setFillColor(C_MID)
        c.roundRect(0, 0, 4, self.H, 2, fill=1, stroke=0)
        c.setFillColor(C_DEEP)
        c.setFont('Helvetica-Bold', 9)
        c.drawString(14, 6, self.title.upper())


# ── Main PDF Generation Function ──────────────────────────────────────────────
def generate_candidate_detail_pdf(candidate, company, total_attempts, submitted_count,
                                  passed_count, failed_count, best_score, avg_score,
                                  pass_pct, attempts, extra_details, latest_test_category,
                                  response):
    """
    Generate a professional single-candidate detail report.
    """
    PAGE_W = 540 # letter 612 - 36*2 margins
    current_time_str = timezone.now().strftime("%B %d, %Y  %I:%M %p")

    doc = SimpleDocTemplate(
        response,
        pagesize=letter,
        rightMargin=36, leftMargin=36,
        topMargin=50,   bottomMargin=40,
        title=f"{company.name} – Candidate Report: {candidate.name}",
        author=company.name,
    )

    story = []

    # Title & Header Block
    story.append(Paragraph(f"{candidate.name}", TITLE_S))
    story.append(Paragraph(f"{candidate.email}  ·  Registered On: {timezone.localtime(candidate.created_at).strftime('%B %d, %Y')}", SUB_S))
    story.append(HRFlowable(width=PAGE_W, thickness=1.5, color=C_MID, spaceBefore=4, spaceAfter=14))

    # Stats cards row
    stat_data = [
        ("Total Attempts", total_attempts, C_MID),
        ("Submitted", submitted_count, C_MID),
        ("Passed", passed_count, C_PASS),
        ("Failed", failed_count, C_FAIL),
        ("Best Score", f"{best_score}%", C_WARN)
    ]
    story.append(_StatCards(stat_data, PAGE_W))
    story.append(Spacer(1, 14))

    # 1. Candidate Profile Info section
    story.append(_SectionHeader("Candidate Profile", PAGE_W))
    story.append(Spacer(1, 6))

    # Build details grid table
    details_items = [
        [
            Paragraph("FULL NAME", LABEL_S),
            Paragraph("EMAIL ADDRESS", LABEL_S)
        ],
        [
            Paragraph(candidate.name, VAL_S),
            Paragraph(candidate.email, VAL_S)
        ],
        [
            Paragraph("DESIGNATION / TECH", LABEL_S),
            Paragraph("REGISTERED DATE", LABEL_S)
        ],
        [
            Paragraph(candidate.designation_tech or "—", VAL_S),
            Paragraph(timezone.localtime(candidate.created_at).strftime('%b %d, %Y, %I:%M %p'), VAL_S)
        ],
        [
            Paragraph("LATEST TEST CATEGORY", LABEL_S),
            Paragraph("AVERAGE SCORE (PASS %)", LABEL_S)
        ],
        [
            Paragraph(latest_test_category, VAL_S),
            Paragraph(f"{avg_score}%  (Pass: {pass_pct}%)" if submitted_count else "—", VAL_S)
        ]
    ]

    details_table = Table(details_items, colWidths=[270, 270])
    details_table.setStyle(TableStyle([
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('LINEBELOW', (0, 1), (1, 1), 0.5, C_RULE),
        ('LINEBELOW', (0, 3), (1, 3), 0.5, C_RULE),
        ('LINEBELOW', (0, 5), (1, 5), 0.5, C_RULE),
        ('TOPPADDING', (0, 2), (-1, 2), 6),
        ('TOPPADDING', (0, 4), (-1, 4), 6),
    ]))
    story.append(details_table)
    story.append(Spacer(1, 14))

    # Extra/Additional details if present
    if extra_details:
        story.append(_SectionHeader("Additional Form Details", PAGE_W))
        story.append(Spacer(1, 6))
        
        extra_rows = []
        # Group extra fields into 2 columns
        items_list = list(extra_details.items())
        for idx in range(0, len(items_list), 2):
            row_items = []
            # Col 1
            k1, v1 = items_list[idx]
            row_items.append(Paragraph(f"{k1.upper()}: <b>{v1}</b>", CELL_S))
            # Col 2
            if idx + 1 < len(items_list):
                k2, v2 = items_list[idx + 1]
                row_items.append(Paragraph(f"{k2.upper()}: <b>{v2}</b>", CELL_S))
            else:
                row_items.append(Paragraph("", CELL_S))
            extra_rows.append(row_items)

        extra_table = Table(extra_rows, colWidths=[270, 270])
        extra_table.setStyle(TableStyle([
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('LINEBELOW', (0, 0), (-1, -1), 0.5, C_RULE),
        ]))
        story.append(extra_table)
        story.append(Spacer(1, 14))

    # 2. Attempts Table
    story.append(_SectionHeader("Test Attempts History", PAGE_W))
    story.append(Spacer(1, 6))

    # Attempts column widths: # 30 | Category 140 | Level 90 | Score 70 | Result 80 | Duration 60 | Date 70 = 540
    att_cols = [30, 140, 90, 70, 80, 60, 70]
    att_headers = [
        Paragraph("#", TH_S),
        Paragraph("CATEGORY", TH_S),
        Paragraph("LEVEL", TH_S),
        Paragraph("SCORE", TH_S),
        Paragraph("RESULT", TH_S),
        Paragraph("DURATION", TH_S),
        Paragraph("DATE", TH_S),
    ]
    att_data = [att_headers]

    for counter, attempt in enumerate(attempts, 1):
        pct = float(attempt.percentage)
        
        # Result text
        if not attempt.is_submitted:
            res_p = Paragraph("Pending", PEND_S)
        elif pct >= pass_pct:
            res_p = Paragraph("Passed", CORR_S)
        else:
            res_p = Paragraph("Failed", WRNG_S)

        formatted_date = timezone.localtime(attempt.created_at).strftime("%b %d, %Y")

        # Color-coded score styling
        if pct >= 70:
            score_col = C_PASS
        elif pct >= 50:
            score_col = C_WARN
        else:
            score_col = C_FAIL
        score_p = Paragraph(f"<b>{attempt.percentage}%</b>", _s(f'Sc{attempt.pk}', fontName='Helvetica-Bold', fontSize=8.5, textColor=score_col))

        att_data.append([
            Paragraph(str(counter), BCELL_S),
            Paragraph(attempt.get_test_category_display(), CELL_S),
            Paragraph(attempt.level.capitalize(), CELL_S),
            score_p,
            res_p,
            Paragraph(f"{attempt.duration_minutes} min", CELL_S),
            Paragraph(formatted_date, CELL_S),
        ])

    att_table = Table(att_data, colWidths=att_cols, repeatRows=1)
    att_ts = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), C_MID),
        ('LINEBELOW',  (0, 0), (-1, 0), 1.5, C_HEADER),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LINEBELOW', (0, 1), (-1, -1), 0.5, C_RULE),
    ])

    for i in range(1, len(att_data)):
        bg = C_STRIP if i % 2 == 0 else colors.white
        att_ts.add('BACKGROUND', (0, i), (-1, i), bg)

    att_table.setStyle(att_ts)
    story.append(att_table)

    # Build Doc
    doc.build(
        story,
        canvasmaker=lambda *a, **kw: _DetailCanvas(
            *a,
            company_name=company.name,
            candidate_name=candidate.name,
            generated_at=current_time_str,
            **kw,
        )
    )

"""
dashboard/allampt_exports/details.py
──────────────────────────────────────
Professional single-attempt detail PDF.
Improvements over v1:
  • Two-column candidate info + session-meta block below title
  • Stat cards with coloured accent top-borders (drawn via Flowable)
  • Wider bar chart with score-badge pill
  • Clock gauge with colour-coded arc (green / amber / red)
  • Section headers with left accent stripe
  • Longest-question card with answer choices mini-table
  • Consistent 12 pt section rhythm
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    BaseDocTemplate, Frame, Flowable, HRFlowable,
    PageTemplate, Paragraph, Spacer, Table, TableStyle,
)
from reportlab.pdfgen import canvas as rl_canvas

# ── Palette (unchanged from project theme) ────────────────────────────────────
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
LABEL_S   = _s('L',  fontSize=7, textColor=C_LIGHT, leading=9)
CORR_S    = _s('Cr', fontName='Helvetica-Bold', fontSize=8.5, textColor=C_PASS, leading=11)
WRNG_S    = _s('Wr', fontName='Helvetica-Bold', fontSize=8.5, textColor=C_FAIL, leading=11)
SKIP_S    = _s('Sk', fontName='Helvetica-Bold', fontSize=8.5, textColor=C_SKIP, leading=11)
INFO_S    = _s('I',  fontSize=8, textColor=C_SKY, leading=12)
INFO_B    = _s('IB', fontName='Helvetica-Bold', fontSize=8, textColor=C_DEEP, leading=12)
Q_S       = _s('Q',  fontSize=8.5, leading=13, textColor=C_DEEP)
QMETA_S   = _s('QM', fontName='Helvetica-Bold', fontSize=8, textColor=C_MID, leading=11)


def _hr(width='100%', thick=0.6, color=None, before=2, after=6):
    return HRFlowable(width=width, thickness=thick,
                      color=color or C_RULE,
                      spaceBefore=before, spaceAfter=after)


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
        w, h = A4

        # ── Top bar (gradient-look: two rects) ────────────────────────────
        self.setFillColor(C_DEEP)
        self.rect(0, h - 26, w, 26, fill=1, stroke=0)
        self.setFillColor(C_MID)
        self.rect(0, h - 26, w * 0.45, 26, fill=1, stroke=0)

        # Company badge strip
        self.setFillColor(C_ACC)
        self.rect(0, h - 26, 4, 26, fill=1, stroke=0)

        # Top-bar text
        self.setFillColor(C_WHITE)
        self.setFont('Helvetica-Bold', 8.5)
        self.drawString(12, h - 17, self.company_name.upper())
        self.setFont('Helvetica', 7.5)
        self.setFillColor(colors.HexColor('#90e0ef'))
        self.drawRightString(w - 36, h - 17,
                             f'Attempt Detail  ·  {self.candidate_name}')

        # ── Footer ────────────────────────────────────────────────────────
        self.setFillColor(C_DEEP)
        self.rect(0, 0, w, 22, fill=1, stroke=0)
        self.setFillColor(colors.HexColor('#0077b6'))
        self.rect(0, 0, 4, 22, fill=1, stroke=0)          # left accent pip

        self.setFillColor(C_WHITE)
        self.setFont('Helvetica-Bold', 7)
        self.drawString(12, 7, self.company_name)
        self.setFont('Helvetica', 7)
        self.drawRightString(w - 36, 7,
                             f'Page {self._pageNumber} of {total}')
        self.setFillColor(colors.HexColor('#90e0ef'))
        self.setFont('Helvetica', 6.5)
        self.drawCentredString(w / 2, 7, f'Generated  {self.generated_at}')


# ── Stat card strip ───────────────────────────────────────────────────────────
class _StatCards(Flowable):
    """
    A row of N stat cards, each with a coloured top-border accent,
    a small label and a large value. Much more visually distinct than
    a plain Table background.
    """
    CARD_H  = 68
    ACCENT  = 3    # top-border height

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
            c.drawString(x + 10, self.CARD_H - 16, label.upper())

            # Value
            val_str = str(value)
            font_sz = 18 if len(val_str) <= 6 else 13
            c.setFillColor(C_DEEP)
            c.setFont('Helvetica-Bold', font_sz)
            c.drawString(x + 10, 14, val_str)

            # Separator line between cards
            if i < n - 1:
                c.setStrokeColor(C_RULE)
                c.setLineWidth(0.5)
                c.line(x + w + GAP / 2, 6, x + w + GAP / 2, self.CARD_H - 6)


# ── Section header with left accent stripe ────────────────────────────────────
class _SectionHeader(Flowable):
    H = 22

    def __init__(self, title, width):
        super().__init__()
        self.title = title
        self.width = width
        self.height = self.H

    def draw(self):
        c = self.canv
        # Background band
        c.setFillColor(C_STRIP)
        c.roundRect(0, 0, self.width, self.H, 3, fill=1, stroke=0)
        # Left accent pip
        c.setFillColor(C_MID)
        c.roundRect(0, 0, 4, self.H, 2, fill=1, stroke=0)
        # Title text
        c.setFillColor(C_DEEP)
        c.setFont('Helvetica-Bold', 9.5)
        c.drawString(14, 7, self.title.upper())


# ── Horizontal bar chart (Score vs Pass Threshold) ────────────────────────────
class _BarChart(Flowable):

    def __init__(self, pass_pct, attempt_pct, is_passed, width):
        super().__init__()
        self.pass_pct    = pass_pct
        self.attempt_pct = attempt_pct
        self.is_passed   = is_passed
        self.width       = width
        self.height      = 100

    def draw(self):
        c      = self.canv
        BAR_H  = 20
        BAR_W  = self.width - 60
        BADGE  = 46      # badge pill width

        def _bar(y, pct, fill_col, label):
            # Track
            c.setFillColor(C_GHOST)
            c.roundRect(0, y, BAR_W, BAR_H, 4, fill=1, stroke=0)
            # Fill
            px = max(BAR_W * pct / 100, 0)
            if px > 0:
                c.setFillColor(fill_col)
                c.roundRect(0, y, px, BAR_H, 4, fill=1, stroke=0)
            # Bar label (above)
            c.setFillColor(C_SKY)
            c.setFont('Helvetica', 7)
            c.drawString(0, y + BAR_H + 4, label)
            # Badge pill
            bx = BAR_W + 10
            c.setFillColor(fill_col)
            c.roundRect(bx, y + 2, BADGE, BAR_H - 4, 8, fill=1, stroke=0)
            c.setFillColor(C_WHITE)
            c.setFont('Helvetica-Bold', 8.5)
            c.drawCentredString(bx + BADGE / 2, y + 6, f'{pct:.1f}%')

        att_col = C_PASS if self.is_passed else C_FAIL

        # Section label
        c.setFillColor(C_DEEP)
        c.setFont('Helvetica-Bold', 9)
        c.drawString(0, self.height - 8, 'Score vs Pass Threshold')

        _bar(50, self.pass_pct,    C_MID,    'Pass Threshold')
        _bar(16, self.attempt_pct, att_col,  'Candidate Score')

        # Outcome badge (far right, vertically centred)
        outcome = 'PASSED' if self.is_passed else 'FAILED'
        badge_col = C_PASS if self.is_passed else C_FAIL
        c.setFillColor(badge_col)
        c.roundRect(BAR_W + 10, 4, BADGE, 8, 3, fill=1, stroke=0)
        c.setFillColor(C_WHITE)
        c.setFont('Helvetica-Bold', 5.5)
        c.drawCentredString(BAR_W + 10 + BADGE / 2, 6, outcome)


# ── Clock / time gauge ────────────────────────────────────────────────────────
class _ClockGauge(Flowable):

    def __init__(self, time_pct, time_taken_display, duration_minutes, width):
        super().__init__()
        self.time_pct           = time_pct
        self.time_taken_display = time_taken_display
        self.duration_minutes   = duration_minutes
        self.width              = width
        self.height             = 100

    def draw(self):
        c  = self.canv
        cx = self.width / 2
        cy = 38
        R  = 30

        # Section label
        c.setFillColor(C_DEEP)
        c.setFont('Helvetica-Bold', 9)
        c.drawCentredString(cx, self.height - 8, 'Time Usage')

        # Background ring
        c.setStrokeColor(C_GHOST)
        c.setLineWidth(9)
        c.circle(cx, cy, R, fill=0, stroke=1)

        # Coloured arc
        pct = min(self.time_pct, 100)
        if pct > 95:
            arc_col = C_FAIL
        elif pct > 80:
            arc_col = C_WARN
        else:
            arc_col = C_ACC

        c.setStrokeColor(arc_col)
        c.setLineWidth(10)
        sweep = 360 * pct / 100
        c.arc(cx - R, cy - R, cx + R, cy + R,
              startAng=90, extent=-sweep)

        # Centre text
        c.setFillColor(C_DEEP)
        c.setFont('Helvetica-Bold', 12)
        c.drawCentredString(cx, cy + 4, f'{pct:.0f}%')
        c.setFont('Helvetica', 6.5)
        c.setFillColor(C_LIGHT)
        c.drawCentredString(cx, cy - 7, 'used')

        # Caption below
        c.setFillColor(C_DEEP)
        c.setFont('Helvetica-Bold', 8)
        c.drawCentredString(cx, 8, self.time_taken_display)
        c.setFont('Helvetica', 6.5)
        c.setFillColor(C_LIGHT)
        c.drawCentredString(cx, -1, f'of {self.duration_minutes} min allotted')


# ── Candidate info + session meta two-column block ────────────────────────────
def _info_block(attempt, pass_pct, usable_w):
    """
    Left col: candidate fields (email, level, session type, duration)
    Right col: attempt meta (date, pass mark, total questions)
    """
    cw = usable_w / 2 - 8

    def row(label, value):
        return Table(
            [[Paragraph(label, LABEL_S), Paragraph(str(value), INFO_B)]],
            colWidths=[70, cw - 74],
        )

    from django.utils import timezone
    local_dt = timezone.localtime(attempt.created_at)

    left_rows  = [
        row('Email',    attempt.candidate.email),
        row('Level',    attempt.level.capitalize()),
        row('Session',  attempt.session_type.capitalize()),
        row('Duration', f'{attempt.duration_minutes} min'),
    ]
    right_rows = [
        row('Date',       local_dt.strftime('%b %d, %Y')),
        row('Time',       local_dt.strftime('%I:%M %p')),
        row('Pass Mark',  f'{pass_pct:.1f}%'),
        row('Questions',  attempt.question_count),
    ]

    def col_tbl(rows):
        data = [[r] for r in rows]
        t = Table(data, colWidths=[cw])
        t.setStyle(TableStyle([
            ('TOPPADDING',    (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING',   (0, 0), (-1, -1), 0),
            ('RIGHTPADDING',  (0, 0), (-1, -1), 0),
            ('LINEBELOW',     (0, 0), (-1, -2), 0.4, C_RULE),
        ]))
        return t

    outer = Table(
        [[col_tbl(left_rows), col_tbl(right_rows)]],
        colWidths=[cw + 8, cw + 8],
    )
    outer.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), C_PALE),
        ('TOPPADDING',    (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING',   (0, 0), (-1, -1), 12),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 12),
        ('LINEAFTER',     (0, 0), (0, -1),  0.6, C_RULE),
        ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
        ('BOX',           (0, 0), (-1, -1), 0.6, C_RULE),
        ('ROUNDEDCORNERS', [4]),
    ]))
    return outer


# ── Session breakdown table ───────────────────────────────────────────────────
def _session_table(session_list, page_w):
    cw = [
        page_w * 0.27,
        page_w * 0.11,
        page_w * 0.10,
        page_w * 0.12,
        page_w * 0.12,
        page_w * 0.14,
        page_w * 0.14,
    ]
    hdr = [Paragraph(h, TH_S) for h in
           ['SUBJECT', 'LEVEL', 'TOTAL', 'ATTENDED', 'CORRECT', 'WRONG', 'SKIPPED']]
    data = [hdr]
    for s in session_list:
        data.append([
            Paragraph(s['name'],              BCELL_S),
            Paragraph(s['level'].capitalize(), CELL_S),
            Paragraph(str(s['total']),         CELL_S),
            Paragraph(str(s['attended']),      CELL_S),
            Paragraph(str(s['correct']),       CORR_S),
            Paragraph(str(s['wrong']),         WRNG_S),
            Paragraph(str(s['skipped']),       SKIP_S),
        ])

    tbl = Table(data, colWidths=cw, repeatRows=1)
    ts  = TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0),  C_MID),
        ('LINEBELOW',     (0, 0), (-1, 0),  2,   colors.HexColor('#023e8a')),
        ('TOPPADDING',    (0, 0), (-1, 0),  9),
        ('BOTTOMPADDING', (0, 0), (-1, 0),  9),
        ('LEFTPADDING',   (0, 0), (-1, 0),  8),
        ('RIGHTPADDING',  (0, 0), (-1, 0),  8),
        ('VALIGN',        (0, 1), (-1, -1), 'TOP'),
        ('TOPPADDING',    (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ('LEFTPADDING',   (0, 1), (-1, -1), 8),
        ('RIGHTPADDING',  (0, 1), (-1, -1), 8),
        ('LINEBELOW',     (0, 1), (-1, -1), 0.4, C_RULE),
    ])
    for i in range(1, len(data)):
        ts.add('BACKGROUND', (0, i), (-1, i),
               C_STRIP if i % 2 == 0 else C_WHITE)
    tbl.setStyle(ts)
    return tbl


# ── Longest-question card ─────────────────────────────────────────────────────
def _longest_q_card(lq, page_w):
    """
    Polished card: meta pill row → question text → stats footer bar.
    """
    if lq.get('is_answered') is None or not lq.get('is_answered'):
        outcome_txt, outcome_col = 'SKIPPED', C_SKIP
    elif lq.get('is_correct'):
        outcome_txt, outcome_col = 'CORRECT', C_PASS
    else:
        outcome_txt, outcome_col = 'WRONG', C_FAIL

    # ── Meta pill strip ───────────────────────────────────────────────────
    pill_s = _s('Pill', fontName='Helvetica-Bold', fontSize=7.5,
                textColor=C_WHITE, leading=10)
    def _pill(text, bg):
        t = Table([[Paragraph(text, pill_s)]],
                  colWidths=[None])
        t.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (-1, -1), bg),
            ('TOPPADDING',    (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING',   (0, 0), (-1, -1), 8),
            ('RIGHTPADDING',  (0, 0), (-1, -1), 8),
            ('ROUNDEDCORNERS', [10]),
        ]))
        return t

    pills_row = Table(
        [[_pill(f"Subject: {lq['subject']}", C_MID),
          Spacer(6, 1),
          _pill(f"Subtitle: {lq['subtitle']}", C_SKY),
          Spacer(6, 1),
          _pill(f"Level: {lq['level']}", C_ACC),
          Spacer(6, 1),
          _pill(outcome_txt, outcome_col)]],
        colWidths=None,
    )
    pills_row.setStyle(TableStyle([
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING',    (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('LEFTPADDING',   (0, 0), (-1, -1), 0),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 4),
    ]))

    # ── Stats footer ──────────────────────────────────────────────────────
    stat_s = _s('QStat', fontSize=7.5, textColor=C_SKY, leading=11)
    stat_b = _s('QStatB', fontName='Helvetica-Bold', fontSize=7.5,
                textColor=C_DEEP, leading=11)
    stats_row = Table(
        [[Paragraph('Characters:', stat_s),
          Paragraph(str(lq['char_count']), stat_b),
          Paragraph('Est. read time:', stat_s),
          Paragraph(lq['est_time_display'], stat_b),
          Paragraph('Outcome:', stat_s),
          Paragraph(outcome_txt, _s('OS', fontName='Helvetica-Bold',
                                    fontSize=7.5, textColor=outcome_col, leading=11))]],
        colWidths=[65, 35, 80, 50, 52, 60],
    )
    stats_row.setStyle(TableStyle([
        ('TOPPADDING',    (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('LEFTPADDING',   (0, 0), (-1, -1), 0),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 6),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
    ]))

    # ── Outer card ────────────────────────────────────────────────────────
    card = Table(
        [
            [pills_row],
            [_hr(page_w - 24, thick=0.5, before=4, after=4)],
            [Paragraph(lq['question_full'][:700], Q_S)],
            [_hr(page_w - 24, thick=0.5, before=6, after=4)],
            [stats_row],
        ],
        colWidths=[page_w],
    )
    card.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), C_STRIP),
        ('TOPPADDING',    (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING',   (0, 0), (-1, -1), 12),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 12),
        ('BOX',           (0, 0), (-1, -1), 0.8, C_RULE),
        ('LINEABOVE',     (0, 0), (-1, 0),  3, outcome_col),   # top colour stripe
        ('ROUNDEDCORNERS', [5]),
    ]))
    return card


# ── Public entry point ────────────────────────────────────────────────────────
def generate_attempt_detail_pdf(
    attempt,
    company,
    pass_pct: float,
    attempt_pct: float,
    is_passed: bool,
    time_taken_display: str,
    time_pct: float,
    session_list: list,
    longest_question: dict | None,
    response,
):
    from django.utils import timezone

    PAGE_W, PAGE_H = A4
    L = R = 36
    T = 54          # leaves room under the taller top bar
    B = 36
    UW = PAGE_W - L - R    # ≈ 523 pt usable width

    gen_time = timezone.now().strftime('%B %d, %Y  %I:%M %p')

    doc = BaseDocTemplate(
        response,
        pagesize=A4,
        rightMargin=R, leftMargin=L,
        topMargin=T,   bottomMargin=B,
        title=f'{attempt.candidate.name} – Attempt Detail',
        author=company.name,
    )
    frame = Frame(L, B, UW, PAGE_H - T - B, id='body', showBoundary=0)
    doc.addPageTemplates([PageTemplate(
        id='main', frames=[frame],
        onPage=lambda c, d: None,
    )])

    canvas_kw = dict(
        company_name   = company.name,
        candidate_name = attempt.candidate.name,
        generated_at   = gen_time,
    )

    story = []

    # ── 1. Title block ────────────────────────────────────────────────────
    story.append(Paragraph(attempt.candidate.name, TITLE_S))
    story.append(Paragraph(
        f'Test Attempt Detail Report  ·  {attempt.candidate.email}', SUB_S
    ))
    story.append(_hr(UW, thick=1.5, color=C_MID, before=6, after=12))

    # ── 2. Stat cards ─────────────────────────────────────────────────────
    pass_fail = 'PASSED' if is_passed else 'FAILED'
    pf_col    = C_PASS if is_passed else C_FAIL
    story.append(_StatCards([
        ('Score',     f'{attempt_pct:.1f}%',     C_ACC),
        ('Correct',   attempt.correct_count,      C_PASS),
        ('Wrong',     attempt.wrong_count,         C_FAIL),
        ('Skipped',   getattr(attempt, 'skipped_count', '—'), C_SKIP),
        ('Questions', attempt.question_count,      C_MID),
        (pass_fail,   attempt.level.upper(),       pf_col),
    ], UW))
    story.append(Spacer(1, 14))

    # ── 3. Candidate info + session meta block ─────────────────────────────
    story.append(_info_block(attempt, pass_pct, UW))
    story.append(Spacer(1, 14))

    # ── 4. Charts row (bar + clock) ────────────────────────────────────────
    story.append(_SectionHeader('Performance Overview', UW))
    story.append(Spacer(1, 8))

    left_w  = UW * 0.64
    right_w = UW - left_w - 10

    charts = Table(
        [[_BarChart(pass_pct, attempt_pct, is_passed, left_w - 24),
          _ClockGauge(time_pct, time_taken_display,
                      attempt.duration_minutes, right_w - 24)]],
        colWidths=[left_w, right_w],
    )
    charts.setStyle(TableStyle([
        ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING',    (0, 0), (-1, -1), 14),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 14),
        ('LEFTPADDING',   (0, 0), (-1, -1), 14),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 14),
        ('BACKGROUND',    (0, 0), (-1, -1), C_WHITE),
        ('BOX',           (0, 0), (-1, -1), 0.8, C_RULE),
        ('LINEAFTER',     (0, 0), (0, -1),  0.6, C_RULE),
        ('ROUNDEDCORNERS', [5]),
    ]))
    story.append(charts)
    story.append(Spacer(1, 16))

    # ── 5. Session breakdown ───────────────────────────────────────────────
    if session_list:
        label = ('Single Session Details'
                 if getattr(attempt, 'session_type', 'single') == 'single'
                 else 'Multi-Session Breakdown')
        story.append(_SectionHeader(label, UW))
        story.append(Spacer(1, 8))
        story.append(_session_table(session_list, UW))
        story.append(Spacer(1, 16))

    # ── 6. Longest question card ───────────────────────────────────────────
    if longest_question:
        story.append(_SectionHeader('Longest Question', UW))
        story.append(Spacer(1, 8))
        story.append(_longest_q_card(longest_question, UW))

    # ── Build ──────────────────────────────────────────────────────────────
    doc.build(
        story,
        canvasmaker=lambda *a, **kw: _DetailCanvas(*a, **canvas_kw, **kw),
    )
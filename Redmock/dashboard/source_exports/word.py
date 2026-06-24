from html import escape

from .common import answer_text, option_rows, subject_name, subtitle_name

content_type = 'application/msword; charset=utf-8'
extension = 'doc'

OPTION_LABELS = ['A', 'B', 'C', 'D', 'E', 'F']

LEVEL_COLORS = {
    'easy':   ('#065F46', '#D1FAE5', '◆ Easy'),
    'medium': ('#92400E', '#FEF3C7', '◆ Medium'),
    'hard':   ('#7F1D1D', '#FEE2E2', '◆ Hard'),
}


def _level_badge(quiz):
    level = quiz.get_level_display().lower()
    bg, fg, label_map = {
        'easy':   ('#D1FAE5', '#065F46', '◆ Easy'),
        'medium': ('#FEF3C7', '#92400E', '◆ Medium'),
        'hard':   ('#FEE2E2', '#7F1D1D', '◆ Hard'),
    }.get(level, ('#E2E8F0', '#1E293B', f'◆ {quiz.get_level_display()}'))
    return (
        f'<span style="display:inline-block;padding:2px 10px;border-radius:20px;'
        f'background:{bg};color:{fg};font-size:11px;font-weight:700;'
        f'letter-spacing:.5px;font-family:Inter,Arial,sans-serif;">'
        f'{label_map}</span>'
    )


def build(quizzes, include_answers=False):
    blocks = []

    for index, quiz in enumerate(quizzes, start=1):
        # --- Options ---
        options_html = ''
        for i, (option_key, option_value) in enumerate(option_rows(quiz)):
            label = OPTION_LABELS[i] if i < len(OPTION_LABELS) else option_key
            is_correct = (
                include_answers and
                escape(option_key) == escape(quiz.correct_answer)
            )
            opt_bg     = '#F0FDF4' if is_correct else 'transparent'
            opt_border = '#10B981' if is_correct else '#E2E8F0'
            opt_color  = '#065F46' if is_correct else '#334155'
            lbl_color  = '#10B981' if is_correct else '#2563EB'
            tick       = '  ✓' if is_correct else ''
            options_html += (
                f'<div style="display:flex;align-items:flex-start;'
                f'padding:8px 14px;margin-bottom:6px;border-radius:8px;'
                f'border:1.5px solid {opt_border};background:{opt_bg};">'
                f'<span style="min-width:28px;font-size:13.5px;font-weight:700;'
                f'color:{lbl_color};flex-shrink:0;padding-top:1px;">'
                f'{label}.&nbsp;</span>'
                f'<span style="margin-left:8px;color:{opt_color};font-size:13.5px;'
                f'line-height:1.5;padding-top:1px;">{escape(option_value)}{tick}</span>'
                f'</div>'
            )

        # --- Context paragraph ---
        context_html = ''
        if quiz.question_paragraph:
            context_html = (
                '<div style="background:#EFF6FF;border-left:4px solid #2563EB;'
                'border-radius:0 8px 8px 0;padding:10px 14px;margin-bottom:14px;">'
                f'<p style="margin:0;color:#1E40AF;font-size:13px;font-style:normal;'
                f'line-height:1.6;">{escape(quiz.question_paragraph)}</p>'
                '</div>'
            )

        # --- Answer block ---
        answer_html = ''
        if include_answers:
            answer_html = (
                '<div style="margin-top:14px;padding:10px 16px;'
                'background:#F0FDF4;border-radius:8px;'
                'border:1.5px solid #10B981;">'
                '<span style="color:#065F46;font-weight:700;font-size:13px;">'
                f'✓ Answer: {escape(quiz.correct_answer)}</span>'
                f'<span style="color:#047857;font-size:13px;"> — '
                f'{escape(answer_text(quiz))}</span>'
                '</div>'
            )

        # --- Meta badges row ---
        meta_html = (
            '<div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:14px;">'
            f'<span style="background:#EFF6FF;color:#1E40AF;font-size:11px;'
            f'font-weight:600;padding:3px 10px;border-radius:20px;'
            f'border:1px solid #BFDBFE;">📚 {escape(subject_name(quiz))}</span>'
            f'<span style="background:#F5F3FF;color:#5B21B6;font-size:11px;'
            f'font-weight:600;padding:3px 10px;border-radius:20px;'
            f'border:1px solid #DDD6FE;">🏷 {escape(subtitle_name(quiz))}</span>'
            f'{_level_badge(quiz)}'
            '</div>'
        )

        # --- Question card ---
        blocks.append(
            '<div style="position:relative;background:#FFFFFF;border-radius:12px;'
            'border:1px solid #E2E8F0;padding:24px 28px;margin-bottom:20px;'
            'box-shadow:0 1px 4px rgba(0,0,0,.06);page-break-inside:avoid;">'

            # Ghost number
            f'<div style="position:absolute;top:10px;right:18px;font-size:64px;'
            f'font-weight:900;color:#F1F5F9;font-family:Poppins,Arial,sans-serif;'
            f'line-height:1;user-select:none;">{index:02d}</div>'

            # Question heading
            f'<h2 style="margin:0 0 12px;font-size:15.5px;font-weight:700;'
            f'color:#0F172A;font-family:Poppins,Arial,sans-serif;line-height:1.5;'
            f'padding-right:60px;">'
            f'<span style="color:#2563EB;margin-right:6px;">Q{index}.</span>'
            f'{escape(quiz.question)}</h2>'

            f'{context_html}'
            f'{meta_html}'
            f'<div>{options_html}</div>'
            f'{answer_html}'
            '</div>'
        )

    html = (
        '<html><head>'
        '<meta charset="utf-8">'
        '<link rel="preconnect" href="https://fonts.googleapis.com">'
        '<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;900'
        '&display=swap" rel="stylesheet">'
        '<style>'
        '* { box-sizing: border-box; margin: 0; padding: 0; font-style: normal; }'
        'body {'
        '  font-family: Poppins, Arial, sans-serif;'
        '  background: #F8FAFC;'
        '  color: #1E293B;'
        '  padding: 0;'
        '  margin: 0;'
        '}'
        '.page-wrap {'
        '  max-width: 820px;'
        '  margin: 0 auto;'
        '  padding: 40px 32px 60px;'
        '}'
        '@media print {'
        '  body { background: #fff; }'
        '  .page-wrap { padding: 20px; }'
        '}'
        '</style>'
        '</head><body>'
        '<div class="page-wrap">'

        # Header
        '<div style="margin-bottom:32px;padding-bottom:20px;'
        'border-bottom:2px solid #E2E8F0;">'
        '<div style="display:flex;align-items:center;gap:14px;">'
        '<div>'
        '<h1 style="font-family:Poppins,Arial,sans-serif;font-size:24px;'
        'font-weight:900;color:#0F172A;letter-spacing:-.5px;">'
        'Question Source</h1>'
        '</div>'
        '</div>'
        '</div>'

        f'{"".join(blocks)}'

        # Footer
        '<div style="margin-top:32px;padding-top:16px;border-top:1px solid #E2E8F0;'
        'text-align:center;">'
        '<p style="font-size:11px;color:#94A3B8;">'
        'Generated by Question Source Export · Confidential</p>'
        '</div>'

        '</div>'
        '</body></html>'
    )

    return html.encode('utf-8')

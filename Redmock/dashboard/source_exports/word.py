from html import escape

from .common import answer_text, option_rows, subject_name, subtitle_name

content_type = 'application/msword; charset=utf-8'
extension = 'doc'


def build(quizzes, include_answers=False):
    blocks = []
    for index, quiz in enumerate(quizzes, start=1):
        options = ''.join(
            f'<li><strong>{escape(option_key)}:</strong> {escape(option_value)}</li>'
            for option_key, option_value in option_rows(quiz)
        )
        answer = ''
        if include_answers:
            answer = (
                '<p class="answer"><strong>Answer:</strong> '
                f'{escape(quiz.correct_answer)} - {escape(answer_text(quiz))}</p>'
            )
        context = ''
        if quiz.question_paragraph:
            context = f'<p class="context">{escape(quiz.question_paragraph)}</p>'
        blocks.append(
            '<section class="question">'
            f'<h2>{index}. {escape(quiz.question)}</h2>'
            f'{context}'
            f'<p><strong>Subject:</strong> {escape(subject_name(quiz))}</p>'
            f'<p><strong>Sub Title:</strong> {escape(subtitle_name(quiz))}</p>'
            f'<p><strong>Level:</strong> {escape(quiz.get_level_display())}</p>'
            f'<ol>{options}</ol>'
            f'{answer}'
            '</section>'
        )

    html = (
        '<html><head><meta charset="utf-8">'
        '<style>'
        'body{font-family:Arial,sans-serif;color:#03045e;}'
        '.question{border-bottom:1px solid #90e0ef;padding:14px 0;}'
        'h1{color:#023e8a;} h2{font-size:16px;color:#03045e;}'
        '.context{color:#075985;} .answer{color:#0077b6;}'
        '</style></head><body>'
        '<h1>Question Source</h1>'
        f'{"".join(blocks)}'
        '</body></html>'
    )
    return html.encode('utf-8')

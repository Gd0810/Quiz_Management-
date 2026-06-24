import csv as csvlib
from io import StringIO

from .common import answer_text, subject_name, subtitle_name

content_type = 'text/csv; charset=utf-8'
extension = 'csv'


def build(quizzes, include_answers=False):
    buffer = StringIO()
    fieldnames = [
        'subject',
        'sub_title',
        'level',
        'question_paragraph',
        'question',
        'option_1',
        'option_2',
        'option_3',
        'option_4',
    ]
    if include_answers:
        fieldnames.extend(['correct_answer', 'correct_answer_text'])

    writer = csvlib.DictWriter(buffer, fieldnames=fieldnames)
    writer.writeheader()
    for quiz in quizzes:
        row = {
            'subject': subject_name(quiz),
            'sub_title': subtitle_name(quiz),
            'level': quiz.get_level_display(),
            'question_paragraph': quiz.question_paragraph or '',
            'question': quiz.question,
            'option_1': quiz.option_1,
            'option_2': quiz.option_2,
            'option_3': quiz.option_3,
            'option_4': quiz.option_4,
        }
        if include_answers:
            row['correct_answer'] = quiz.correct_answer
            row['correct_answer_text'] = answer_text(quiz)
        writer.writerow(row)

    return buffer.getvalue().encode('utf-8-sig')

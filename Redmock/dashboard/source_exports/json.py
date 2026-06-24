import json as jsonlib

from .common import answer_text, subject_name, subtitle_name

content_type = 'application/json; charset=utf-8'
extension = 'json'


def build(quizzes, include_answers=False):
    rows = []
    for quiz in quizzes:
        row = {
            'subject': subject_name(quiz),
            'sub_title': subtitle_name(quiz),
            'level': quiz.level,
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
        rows.append(row)
    return jsonlib.dumps(rows, indent=2, ensure_ascii=False).encode('utf-8')

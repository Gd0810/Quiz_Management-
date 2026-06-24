from .common import answer_text, option_rows, subject_name, subtitle_name

content_type = 'text/plain; charset=utf-8'
extension = 'txt'


def build(quizzes, include_answers=False):
    lines = []
    for index, quiz in enumerate(quizzes, start=1):
        lines.append(f'{index}. {quiz.question}')
        if quiz.question_paragraph:
            lines.append(f'Context: {quiz.question_paragraph}')
        lines.append(f'Subject: {subject_name(quiz)}')
        lines.append(f'Sub Title: {subtitle_name(quiz)}')
        lines.append(f'Level: {quiz.get_level_display()}')
        for option_key, option_value in option_rows(quiz):
            lines.append(f'{option_key}: {option_value}')
        if include_answers:
            lines.append(f'Answer: {quiz.correct_answer} - {answer_text(quiz)}')
        lines.append('')
    return '\n'.join(lines).encode('utf-8')

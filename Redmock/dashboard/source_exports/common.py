def option_rows(quiz):
    return [
        ('option_1', quiz.option_1),
        ('option_2', quiz.option_2),
        ('option_3', quiz.option_3),
        ('option_4', quiz.option_4),
    ]


def answer_text(quiz):
    option_map = dict(option_rows(quiz))
    return option_map.get(quiz.correct_answer, '')


def subject_name(quiz):
    return quiz.test_subject.subject


def subtitle_name(quiz):
    return quiz.sub_title.title if quiz.sub_title else 'General'

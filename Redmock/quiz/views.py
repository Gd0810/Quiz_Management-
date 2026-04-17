from datetime import timedelta
from decimal import Decimal

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from dashboard.models import Quiz

from .forms import CandidateStartForm
from .models import Candidate, CandidateTestAttempt


def start_test(request):
    form = CandidateStartForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        candidate, _ = Candidate.objects.get_or_create(
            email=form.cleaned_data['candidate_email'],
            defaults={
                'name': form.cleaned_data['candidate_name'],
                'designation_tech': form.cleaned_data['designation_tech'],
            },
        )
        candidate.name = form.cleaned_data['candidate_name']
        candidate.designation_tech = form.cleaned_data['designation_tech']
        candidate.save(update_fields=['name', 'designation_tech'])

        subjects = list(form.cleaned_data['subjects'])
        subtitles = list(form.cleaned_data['sub_titles'])
        company = subjects[0].company

        quiz_queryset = Quiz.objects.filter(
            test_subject__in=subjects,
            level=form.cleaned_data['level'],
        ).select_related('test_subject', 'sub_title')
        if subtitles:
            quiz_queryset = quiz_queryset.filter(sub_title__in=subtitles)

        selected_questions = list(quiz_queryset.order_by('id')[: form.cleaned_data['question_count']])
        if not selected_questions:
            form.add_error(None, 'No quiz questions found for the selected filters.')
        else:
            answers_json = [
                {'question_id': question.id, 'selected_answer': ''}
                for question in selected_questions
            ]
            attempt = CandidateTestAttempt.objects.create(
                candidate=candidate,
                company=company,
                session_type=form.cleaned_data['session_type'],
                level=form.cleaned_data['level'],
                question_count=len(selected_questions),
                duration_minutes=form.cleaned_data['duration_minutes'],
                selected_subjects=[subject.id for subject in subjects],
                selected_sub_titles=[subtitle.id for subtitle in subtitles],
                answers_json=answers_json,
                started_at=timezone.now(),
            )
            return redirect('quiz:take', attempt_id=attempt.id)

    return render(request, 'quiz/start_test.html', {'form': form})


def take_test(request, attempt_id):
    attempt = get_object_or_404(CandidateTestAttempt.objects.select_related('candidate', 'company'), pk=attempt_id)
    answer_rows = attempt.answers_json or []
    question_ids = [row['question_id'] for row in answer_rows]
    questions = list(Quiz.objects.filter(id__in=question_ids).select_related('test_subject', 'sub_title'))
    question_map = {question.id: question for question in questions}
    ordered_questions = [question_map[qid] for qid in question_ids if qid in question_map]

    if request.method == 'POST':
        updated_answers = []
        correct_count = 0
        for row in answer_rows:
            question_id = row['question_id']
            selected_answer = request.POST.get(f'question_{question_id}', '')
            question = question_map.get(question_id)
            if question and selected_answer == question.correct_answer:
                correct_count += 1
            updated_answers.append(
                {'question_id': question_id, 'selected_answer': selected_answer}
            )

        total_questions = len(updated_answers)
        wrong_count = max(total_questions - correct_count, 0)
        percentage = Decimal('0.00')
        if total_questions:
            percentage = (Decimal(correct_count) / Decimal(total_questions)) * Decimal('100')

        attempt.answers_json = updated_answers
        attempt.correct_count = correct_count
        attempt.wrong_count = wrong_count
        attempt.percentage = percentage.quantize(Decimal('0.01'))
        attempt.submitted_at = timezone.now()
        attempt.is_submitted = True
        attempt.save(
            update_fields=[
                'answers_json',
                'correct_count',
                'wrong_count',
                'percentage',
                'submitted_at',
                'is_submitted',
            ]
        )
        messages.success(request, 'Test submitted successfully.')
        return redirect('quiz:result', attempt_id=attempt.id)

    initial_answers = {row['question_id']: row.get('selected_answer', '') for row in answer_rows}
    context = {
        'attempt': attempt,
        'questions': ordered_questions,
        'initial_answers': initial_answers,
        'end_time_iso': (
            attempt.started_at + timedelta(minutes=attempt.duration_minutes)
        ).isoformat()
        if attempt.started_at
        else '',
    }
    return render(request, 'quiz/take_test.html', context)


def test_result(request, attempt_id):
    attempt = get_object_or_404(
        CandidateTestAttempt.objects.select_related('candidate', 'company'),
        pk=attempt_id,
    )
    answer_rows = attempt.answers_json or []
    question_ids = [row['question_id'] for row in answer_rows]
    question_map = {
        question.id: question for question in Quiz.objects.filter(id__in=question_ids)
    }
    results = []
    for row in answer_rows:
        question = question_map.get(row['question_id'])
        if not question:
            continue
        selected_answer = row.get('selected_answer')
        results.append(
            {
                'question': question,
                'selected_answer': selected_answer,
                'is_correct': selected_answer == question.correct_answer,
            }
        )

    return render(
        request,
        'quiz/result.html',
        {'attempt': attempt, 'results': results},
    )

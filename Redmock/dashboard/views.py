from django.contrib import messages
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render

from quiz.models import Candidate, CandidateTestAttempt

from .forms import CandidateForm, CandidateTestAttemptForm, QuizForm, SubTitleForm, TestSubjectForm
from .models import Quiz, SubTitle, TestSubject


def dashboard_home(request):
    context = {
        'subject_count': TestSubject.objects.count(),
        'subtitle_count': SubTitle.objects.count(),
        'quiz_count': Quiz.objects.count(),
        'candidate_count': Candidate.objects.count(),
        'attempt_count': CandidateTestAttempt.objects.count(),
        'subjects': TestSubject.objects.select_related('company').annotate(
            quiz_total=Count('quizzes')
        )[:6],
        'recent_attempts': CandidateTestAttempt.objects.select_related(
            'candidate', 'company'
        )[:8],
    }
    return render(request, 'dashboard/home.html', context)


def render_crud_list(request, *, queryset, title, create_url, edit_url_name, delete_url_name, fields):
    context = {
        'title': title,
        'objects': queryset,
        'create_url': create_url,
        'edit_url_name': edit_url_name,
        'delete_url_name': delete_url_name,
        'fields': fields,
    }
    return render(request, 'dashboard/crud_list.html', context)


def render_crud_form(request, *, form, title, cancel_url):
    return render(
        request,
        'dashboard/crud_form.html',
        {'form': form, 'title': title, 'cancel_url': cancel_url},
    )


def render_crud_delete(request, *, obj, title, cancel_url):
    return render(
        request,
        'dashboard/crud_delete.html',
        {'object': obj, 'title': title, 'cancel_url': cancel_url},
    )


def subject_list(request):
    queryset = TestSubject.objects.select_related('company').all()
    return render_crud_list(
        request,
        queryset=queryset,
        title='Test Subjects',
        create_url='dashboard:subject_create',
        edit_url_name='dashboard:subject_update',
        delete_url_name='dashboard:subject_delete',
        fields=['company', 'subject', 'created_at'],
    )


def subject_create(request):
    form = TestSubjectForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Test subject created successfully.')
        return redirect('dashboard:subject_list')
    return render_crud_form(
        request,
        form=form,
        title='Create Test Subject',
        cancel_url='dashboard:subject_list',
    )


def subject_update(request, pk):
    subject = get_object_or_404(TestSubject, pk=pk)
    form = TestSubjectForm(request.POST or None, instance=subject)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Test subject updated successfully.')
        return redirect('dashboard:subject_list')
    return render_crud_form(
        request,
        form=form,
        title='Edit Test Subject',
        cancel_url='dashboard:subject_list',
    )


def subject_delete(request, pk):
    subject = get_object_or_404(TestSubject, pk=pk)
    if request.method == 'POST':
        subject.delete()
        messages.success(request, 'Test subject deleted successfully.')
        return redirect('dashboard:subject_list')
    return render_crud_delete(
        request,
        obj=subject,
        title='Delete Test Subject',
        cancel_url='dashboard:subject_list',
    )


def subtitle_list(request):
    queryset = SubTitle.objects.select_related('test_subject', 'test_subject__company').all()
    return render_crud_list(
        request,
        queryset=queryset,
        title='Sub Titles',
        create_url='dashboard:subtitle_create',
        edit_url_name='dashboard:subtitle_update',
        delete_url_name='dashboard:subtitle_delete',
        fields=['test_subject', 'title', 'created_at'],
    )


def subtitle_create(request):
    form = SubTitleForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Sub title created successfully.')
        return redirect('dashboard:subtitle_list')
    return render_crud_form(
        request,
        form=form,
        title='Create Sub Title',
        cancel_url='dashboard:subtitle_list',
    )


def subtitle_update(request, pk):
    subtitle = get_object_or_404(SubTitle, pk=pk)
    form = SubTitleForm(request.POST or None, instance=subtitle)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Sub title updated successfully.')
        return redirect('dashboard:subtitle_list')
    return render_crud_form(
        request,
        form=form,
        title='Edit Sub Title',
        cancel_url='dashboard:subtitle_list',
    )


def subtitle_delete(request, pk):
    subtitle = get_object_or_404(SubTitle, pk=pk)
    if request.method == 'POST':
        subtitle.delete()
        messages.success(request, 'Sub title deleted successfully.')
        return redirect('dashboard:subtitle_list')
    return render_crud_delete(
        request,
        obj=subtitle,
        title='Delete Sub Title',
        cancel_url='dashboard:subtitle_list',
    )


def quiz_list(request):
    queryset = Quiz.objects.select_related('test_subject', 'sub_title').all()
    return render_crud_list(
        request,
        queryset=queryset,
        title='Quizzes',
        create_url='dashboard:quiz_create',
        edit_url_name='dashboard:quiz_update',
        delete_url_name='dashboard:quiz_delete',
        fields=['test_subject', 'sub_title', 'level', 'question', 'correct_answer'],
    )


def quiz_create(request):
    form = QuizForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Quiz question created successfully.')
        return redirect('dashboard:quiz_list')
    return render_crud_form(
        request,
        form=form,
        title='Create Quiz Question',
        cancel_url='dashboard:quiz_list',
    )


def quiz_update(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk)
    form = QuizForm(request.POST or None, request.FILES or None, instance=quiz)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Quiz question updated successfully.')
        return redirect('dashboard:quiz_list')
    return render_crud_form(
        request,
        form=form,
        title='Edit Quiz Question',
        cancel_url='dashboard:quiz_list',
    )


def quiz_delete(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk)
    if request.method == 'POST':
        quiz.delete()
        messages.success(request, 'Quiz question deleted successfully.')
        return redirect('dashboard:quiz_list')
    return render_crud_delete(
        request,
        obj=quiz,
        title='Delete Quiz Question',
        cancel_url='dashboard:quiz_list',
    )


def candidate_list(request):
    queryset = Candidate.objects.all()
    return render_crud_list(
        request,
        queryset=queryset,
        title='Candidates',
        create_url='dashboard:candidate_create',
        edit_url_name='dashboard:candidate_update',
        delete_url_name='dashboard:candidate_delete',
        fields=['name', 'email', 'designation_tech', 'created_at'],
    )


def candidate_create(request):
    form = CandidateForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Candidate created successfully.')
        return redirect('dashboard:candidate_list')
    return render_crud_form(
        request,
        form=form,
        title='Create Candidate',
        cancel_url='dashboard:candidate_list',
    )


def candidate_update(request, pk):
    candidate = get_object_or_404(Candidate, pk=pk)
    form = CandidateForm(request.POST or None, instance=candidate)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Candidate updated successfully.')
        return redirect('dashboard:candidate_list')
    return render_crud_form(
        request,
        form=form,
        title='Edit Candidate',
        cancel_url='dashboard:candidate_list',
    )


def candidate_delete(request, pk):
    candidate = get_object_or_404(Candidate, pk=pk)
    if request.method == 'POST':
        candidate.delete()
        messages.success(request, 'Candidate deleted successfully.')
        return redirect('dashboard:candidate_list')
    return render_crud_delete(
        request,
        obj=candidate,
        title='Delete Candidate',
        cancel_url='dashboard:candidate_list',
    )


def attempt_list(request):
    queryset = CandidateTestAttempt.objects.select_related('candidate', 'company').all()
    return render_crud_list(
        request,
        queryset=queryset,
        title='Candidate Test Attempts',
        create_url='dashboard:attempt_create',
        edit_url_name='dashboard:attempt_update',
        delete_url_name='dashboard:attempt_delete',
        fields=[
            'candidate',
            'company',
            'session_type',
            'level',
            'question_count',
            'percentage',
            'is_submitted',
        ],
    )


def attempt_create(request):
    form = CandidateTestAttemptForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Candidate test attempt created successfully.')
        return redirect('dashboard:attempt_list')
    return render_crud_form(
        request,
        form=form,
        title='Create Candidate Test Attempt',
        cancel_url='dashboard:attempt_list',
    )


def attempt_update(request, pk):
    attempt = get_object_or_404(CandidateTestAttempt, pk=pk)
    form = CandidateTestAttemptForm(request.POST or None, instance=attempt)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Candidate test attempt updated successfully.')
        return redirect('dashboard:attempt_list')
    return render_crud_form(
        request,
        form=form,
        title='Edit Candidate Test Attempt',
        cancel_url='dashboard:attempt_list',
    )


def attempt_delete(request, pk):
    attempt = get_object_or_404(CandidateTestAttempt, pk=pk)
    if request.method == 'POST':
        attempt.delete()
        messages.success(request, 'Candidate test attempt deleted successfully.')
        return redirect('dashboard:attempt_list')
    return render_crud_delete(
        request,
        obj=attempt,
        title='Delete Candidate Test Attempt',
        cancel_url='dashboard:attempt_list',
    )

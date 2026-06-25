import json
from collections import Counter

from django.contrib import messages
from django.contrib.auth.hashers import check_password
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.text import slugify
from functools import wraps

from quiz.models import Candidate, CandidateTestAttempt

from .forms import (
    CandidateForm,
    CandidateFormFieldForm,
    CandidateTestAttemptForm,
    BulkQuestionUploadForm,
    CompanyInstructionsForm,
    CompanyMailSettingsForm,
    CompanySecurityForm,
    QuizForm,
    SubTitleInlineFormSet,
    TestSubjectForm,
)
from .models import CandidateFormField, Company, Quiz, SubTitle, TestSubject
from .source_exports import EXPORTERS


def get_logged_in_company(request):
    company_id = request.session.get('company_id')
    if not company_id:
        return None
    return Company.objects.filter(id=company_id, is_active=True).first()


def company_login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        company = get_logged_in_company(request)
        if not company:
            return redirect(f"{reverse('dashboard:login')}?next={request.path}")
        request.company = company
        return view_func(request, *args, **kwargs)

    return wrapper


def _parse_positive_int(raw_value, default=0):
    try:
        value = int(raw_value)
    except (TypeError, ValueError):
        return default
    return max(value, 0)


def landing_page(request):
    return render(
        request,
        'landing.html',
        {
            'company_count': Company.objects.filter(is_active=True).count(),
            'subject_count': TestSubject.objects.count(),
            'quiz_count': Quiz.objects.count(),
        },
    )


def dashboard_login(request):
    if get_logged_in_company(request):
        return redirect('dashboard:home')

    error = None
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '').strip()
        company = Company.objects.filter(email=email, is_active=True).first()

        if not email or not password:
            error = 'Please enter email and password.'
        elif not company:
            error = 'Company account not found.'
        elif not check_password(password, company.password):
            error = 'Invalid password.'
        else:
            request.session.flush()
            request.session['company_id'] = company.id
            request.session.set_expiry(60 * 60 * 8)
            messages.success(request, f'Welcome back, {company.name}.')
            return redirect(request.GET.get('next') or 'dashboard:home')

    return render(request, 'dashboard/login.html', {'error': error})


def dashboard_logout(request):
    request.session.flush()
    messages.success(request, 'You have been logged out.')
    return redirect('dashboard:login')


@company_login_required
def dashboard_home(request):
    company = request.company
    context = {
        'subject_count': TestSubject.objects.filter(company=company).count(),
        'subtitle_count': SubTitle.objects.filter(test_subject__company=company).count(),
        'quiz_count': Quiz.objects.filter(test_subject__company=company).count(),
        'candidate_count': Candidate.objects.filter(attempts__company=company).distinct().count(),
        'attempt_count': CandidateTestAttempt.objects.filter(company=company).count(),
        'subjects': TestSubject.objects.filter(company=company).select_related('company').annotate(
            quiz_total=Count('quizzes')
        )[:6],
        'recent_attempts': CandidateTestAttempt.objects.filter(company=company).select_related(
            'candidate', 'company'
        )[:8],
        'company': company,
    }
    return render(request, 'dashboard/home.html', context)


@company_login_required
def company_instructions(request):
    form = CompanyInstructionsForm(request.POST or None, instance=request.company)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Test instructions updated successfully.')
        return redirect('dashboard:company_instructions')

    return render(
        request,
        'dashboard/instructions_settings.html',
        {'form': form, 'title': 'Test Instructions', 'cancel_url': 'dashboard:home'},
    )


@company_login_required
def company_settings(request):
    form = CompanySecurityForm(request.POST or None, instance=request.company)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Exam security settings updated successfully.')
        return redirect('dashboard:company_settings')

    return render(
        request,
        'dashboard/security_settings.html',
        {'form': form, 'title': 'Exam Security Settings', 'cancel_url': 'dashboard:home'},
    )


@company_login_required
def company_mail_settings(request):
    form = CompanyMailSettingsForm(request.POST or None, instance=request.company)
    if request.method == 'POST' and form.is_valid():
        company = form.save()
        print(
            '[Redmock Mail] settings saved: '
            f'company={company.name!r}, enabled={company.mail_sender_enabled}, '
            f'host_set={bool(company.smtp_host)}, port={company.smtp_port}, '
            f'username_set={bool(company.smtp_username)}, app_key_set={bool(company.smtp_app_key)}, '
            f'use_tls={company.smtp_use_tls}, ready={company.mail_sender_ready}',
            flush=True,
        )
        messages.success(request, 'Mail settings updated successfully.')
        return redirect('dashboard:company_mail_settings')

    return render(
        request,
        'dashboard/mail_settings.html',
        {'form': form, 'title': 'Mail Settings', 'cancel_url': 'dashboard:home'},
    )


@company_login_required
def candidate_form_field_list(request):
    queryset = CandidateFormField.objects.filter(company=request.company)
    return render(
        request,
        'dashboard/forms_control_list.html',
        {'title': 'Forms Control', 'objects': queryset},
    )


@company_login_required
def candidate_form_field_create(request):
    form = CandidateFormFieldForm(request.POST or None, company=request.company)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Candidate form field created successfully.')
        return redirect('dashboard:candidate_form_field_list')
    return render(
        request,
        'dashboard/forms_control_form.html',
        {'form': form, 'title': 'Create Candidate Form Field', 'cancel_url': 'dashboard:candidate_form_field_list'},
    )


@company_login_required
def candidate_form_field_update(request, pk):
    form_field = get_object_or_404(CandidateFormField, pk=pk, company=request.company)
    form = CandidateFormFieldForm(request.POST or None, instance=form_field, company=request.company)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Candidate form field updated successfully.')
        return redirect('dashboard:candidate_form_field_list')
    return render(
        request,
        'dashboard/forms_control_form.html',
        {'form': form, 'title': 'Edit Candidate Form Field', 'cancel_url': 'dashboard:candidate_form_field_list'},
    )


@company_login_required
def candidate_form_field_delete(request, pk):
    form_field = get_object_or_404(CandidateFormField, pk=pk, company=request.company)
    if request.method == 'POST':
        form_field.delete()
        messages.success(request, 'Candidate form field deleted successfully.')
        return redirect('dashboard:candidate_form_field_list')
    return render(
        request,
        'dashboard/forms_control_delete.html',
        {'object': form_field, 'title': 'Delete Candidate Form Field', 'cancel_url': 'dashboard:candidate_form_field_list'},
    )


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


def render_crud_form(request, *, form, title, cancel_url, use_tinymce=False):
    return render(
        request,
        'dashboard/crud_form.html',
        {'form': form, 'title': title, 'cancel_url': cancel_url, 'use_tinymce': use_tinymce},
    )


def render_crud_delete(request, *, obj, title, cancel_url):
    return render(
        request,
        'dashboard/crud_delete.html',
        {'object': obj, 'title': title, 'cancel_url': cancel_url},
    )


@company_login_required
def subject_list(request):
    base_queryset = TestSubject.objects.filter(company=request.company).prefetch_related('sub_titles')
    all_subjects = list(base_queryset)
    subject_by_id = {subject.id: subject for subject in all_subjects}
    attempts = CandidateTestAttempt.objects.filter(company=request.company).values_list('selected_subjects', flat=True)
    subject_attempt_counts = Counter()
    for selected_subjects in attempts:
        for subject_id in selected_subjects or []:
            try:
                subject_attempt_counts[int(subject_id)] += 1
            except (TypeError, ValueError):
                continue

    chart_rows = [
        {
            'label': subject_by_id[subject_id].subject,
            'count': count,
            'svg': subject_by_id[subject_id].subject_svg or '',
        }
        for subject_id, count in subject_attempt_counts.most_common()
        if subject_id in subject_by_id
    ][:7]
    most_attempted = chart_rows[0]['label'] if chart_rows else 'No attempts yet'

    search_query = request.GET.get('q', '').strip()
    subtitle_filter = request.GET.get('subtitle_filter', 'all')
    sort_by = request.GET.get('sort', 'subject')

    queryset = TestSubject.objects.filter(company=request.company).annotate(subtitle_count=Count('sub_titles')).prefetch_related('sub_titles')
    if search_query:
        queryset = queryset.filter(
            Q(subject__icontains=search_query) | Q(sub_titles__title__icontains=search_query)
        ).distinct()
    if subtitle_filter == 'with':
        queryset = queryset.filter(subtitle_count__gt=0)
    elif subtitle_filter == 'without':
        queryset = queryset.filter(subtitle_count=0)

    if sort_by == 'newest':
        queryset = queryset.order_by('-created_at')
    elif sort_by == 'subtitles':
        queryset = queryset.order_by('-subtitle_count', 'subject')
    else:
        sort_by = 'subject'
        queryset = queryset.order_by('subject')

    query_params = request.GET.copy()
    query_params.pop('page', None)
    querystring = query_params.urlencode()
    page_query_prefix = f'{querystring}&' if querystring else ''

    paginator = Paginator(queryset, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    page_numbers = paginator.get_elided_page_range(page_obj.number, on_each_side=2, on_ends=1)
    return render(
        request,
        'dashboard/subject_list.html',
        {
            'title': 'Test Subjects',
            'objects': page_obj.object_list,
            'page_obj': page_obj,
            'subject_total': len(all_subjects),
            'subtitle_total': SubTitle.objects.filter(test_subject__company=request.company).count(),
            'subject_with_subtitles_total': sum(1 for subject in all_subjects if subject.sub_titles.all()),
            'subject_attempt_total': sum(subject_attempt_counts.values()),
            'most_attempted_subject': most_attempted,
            'chart_labels_json': json.dumps([row['label'] for row in chart_rows]),
            'chart_counts_json': json.dumps([row['count'] for row in chart_rows]),
            'chart_svgs_json': json.dumps([row['svg'] for row in chart_rows]),
            'search_query': search_query,
            'subtitle_filter': subtitle_filter,
            'sort_by': sort_by,
            'page_query_prefix': page_query_prefix,
            'page_numbers': page_numbers,
        },
    )


@company_login_required
def subject_create(request):
    form = TestSubjectForm(request.POST or None)
    formset = SubTitleInlineFormSet(request.POST or None)
    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        subject = form.save(commit=False)
        subject.company = request.company
        subject.save()
        formset.instance = subject
        formset.save()
        messages.success(request, 'Test subject created successfully.')
        return redirect('dashboard:subject_list')
    return render(
        request,
        'dashboard/subject_form.html',
        {'form': form, 'formset': formset, 'title': 'Create Test Subject', 'cancel_url': 'dashboard:subject_list'},
    )


@company_login_required
def subject_update(request, pk):
    subject = get_object_or_404(TestSubject, pk=pk, company=request.company)
    form = TestSubjectForm(request.POST or None, instance=subject)
    formset = SubTitleInlineFormSet(request.POST or None, instance=subject)
    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        form.save()
        formset.save()
        messages.success(request, 'Test subject updated successfully.')
        return redirect('dashboard:subject_list')
    return render(
        request,
        'dashboard/subject_form.html',
        {'form': form, 'formset': formset, 'title': 'Edit Test Subject', 'cancel_url': 'dashboard:subject_list'},
    )


@company_login_required
def subject_delete(request, pk):
    subject = get_object_or_404(TestSubject, pk=pk, company=request.company)
    if request.method == 'POST':
        subject.delete()
        messages.success(request, 'Test subject deleted successfully.')
        return redirect('dashboard:subject_list')
    return render(
        request,
        'dashboard/subject_delete.html',
        {'object': subject, 'title': 'Delete Test Subject', 'cancel_url': 'dashboard:subject_list'},
    )


def _validation_error_text(error):
    if hasattr(error, 'messages'):
        return ' '.join(error.messages)
    return str(error)


def _subtitles_json_for_company(company):
    subtitles = SubTitle.objects.filter(test_subject__company=company).select_related('test_subject')
    return json.dumps([
        {
            'id': subtitle.id,
            'subject_id': subtitle.test_subject_id,
            'title': subtitle.title,
        }
        for subtitle in subtitles
    ])


@company_login_required
def subject_question_upload(request):
    initial = {}
    subject_id = request.GET.get('subject')
    if subject_id:
        selected_subject = TestSubject.objects.filter(pk=subject_id, company=request.company).first()
        if selected_subject:
            initial['test_subject'] = selected_subject

    form = BulkQuestionUploadForm(
        request.POST or None,
        request.FILES or None,
        company=request.company,
        initial=initial,
    )
    subtitles_json = _subtitles_json_for_company(request.company)

    if request.method == 'POST' and form.is_valid():
        upload = form.save()
        try:
            imported_count = upload.import_questions()
        except ValidationError as exc:
            upload.delete()
            form.add_error(None, _validation_error_text(exc))
        else:
            subtitle_name = upload.sub_title.title if upload.sub_title else 'General'
            messages.success(
                request,
                f'{imported_count} questions uploaded for {upload.test_subject.subject} / {subtitle_name} / {upload.get_level_display()}.',
            )
            return redirect('dashboard:subject_list')

    return render(
        request,
        'dashboard/bulk_question_upload.html',
        {
            'title': 'Upload Questions',
            'form': form,
            'subtitles_json': subtitles_json,
        },
    )


@company_login_required
def quiz_list(request):
    base_queryset = Quiz.objects.filter(test_subject__company=request.company).select_related('test_subject', 'sub_title')
    level_counts = dict(
        base_queryset.values('level').annotate(total=Count('id')).values_list('level', 'total')
    )
    total_quiz_count = sum(level_counts.values())
    level_rows = [
        {
            'value': value,
            'label': label,
            'count': level_counts.get(value, 0),
            'percent': round((level_counts.get(value, 0) / total_quiz_count) * 100, 1) if total_quiz_count else 0,
        }
        for value, label in Quiz.LEVEL_CHOICES
    ]

    search_query = request.GET.get('q', '').strip()
    level_filter = request.GET.get('level', 'all')
    subject_filter = request.GET.get('subject', 'all')

    queryset = base_queryset
    if search_query:
        queryset = queryset.filter(
            Q(question__icontains=search_query) | Q(question_paragraph__icontains=search_query)
        )
    if level_filter != 'all':
        valid_levels = {value for value, _label in Quiz.LEVEL_CHOICES}
        if level_filter in valid_levels:
            queryset = queryset.filter(level=level_filter)
        else:
            level_filter = 'all'
    if subject_filter != 'all':
        subject_id = _parse_positive_int(subject_filter)
        if TestSubject.objects.filter(pk=subject_id, company=request.company).exists():
            queryset = queryset.filter(test_subject_id=subject_id)
        else:
            subject_filter = 'all'

    queryset = queryset.order_by('test_subject__subject', 'sub_title__title', 'level', 'id')
    query_params = request.GET.copy()
    query_params.pop('page', None)
    querystring = query_params.urlencode()
    page_query_prefix = f'{querystring}&' if querystring else ''

    paginator = Paginator(queryset, 40)
    page_obj = paginator.get_page(request.GET.get('page'))
    page_numbers = paginator.get_elided_page_range(page_obj.number, on_each_side=2, on_ends=1)

    return render(
        request,
        'dashboard/quiz_list.html',
        {
            'title': 'Quizzes',
            'objects': page_obj.object_list,
            'page_obj': page_obj,
            'page_numbers': page_numbers,
            'page_query_prefix': page_query_prefix,
            'total_quiz_count': total_quiz_count,
            'level_rows': level_rows,
            'level_choices': Quiz.LEVEL_CHOICES,
            'subjects': TestSubject.objects.filter(company=request.company).order_by('subject'),
            'search_query': search_query,
            'level_filter': level_filter,
            'subject_filter': subject_filter,
            'level_chart_labels_json': json.dumps([row['label'] for row in level_rows]),
            'level_chart_counts_json': json.dumps([row['count'] for row in level_rows]),
            'level_chart_percents_json': json.dumps([row['percent'] for row in level_rows]),
        },
    )


@company_login_required
def quiz_create(request):
    form = QuizForm(request.POST or None, request.FILES or None, company=request.company)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Quiz question created successfully.')
        return redirect('dashboard:quiz_list')
    return render(
        request,
        'dashboard/quiz_form.html',
        {
            'form': form,
            'title': 'Create Quiz Question',
            'cancel_url': 'dashboard:quiz_list',
            'subtitles_json': _subtitles_json_for_company(request.company),
        },
    )


@company_login_required
def quiz_update(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk, test_subject__company=request.company)
    form = QuizForm(request.POST or None, request.FILES or None, instance=quiz, company=request.company)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Quiz question updated successfully.')
        return redirect('dashboard:quiz_list')
    return render(
        request,
        'dashboard/quiz_form.html',
        {
            'form': form,
            'title': 'Edit Quiz Question',
            'cancel_url': 'dashboard:quiz_list',
            'subtitles_json': _subtitles_json_for_company(request.company),
        },
    )


@company_login_required
def quiz_delete(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk, test_subject__company=request.company)
    if request.method == 'POST':
        quiz.delete()
        messages.success(request, 'Quiz question deleted successfully.')
        return redirect('dashboard:quiz_list')
    return render(
        request,
        'dashboard/quiz_delete.html',
        {
            'object': quiz,
            'title': 'Delete Quiz Question',
            'cancel_url': 'dashboard:quiz_list',
        },
    )


@company_login_required
def quiz_source_download(request):
    subjects = TestSubject.objects.filter(company=request.company).order_by('subject')
    selected_subject = request.POST.get('subject') or request.GET.get('subject') or 'all'
    selected_level = request.POST.get('level') or request.GET.get('level') or Quiz.LEVEL_BASIC
    answer_mode = request.POST.get('answer_mode') or request.GET.get('answer_mode') or 'without'
    file_type = request.POST.get('file_type')
    errors = []
    question_count_map = {
        'all': {level_value: 0 for level_value, _label in Quiz.LEVEL_CHOICES}
    }

    for subject in subjects:
        question_count_map[str(subject.id)] = {level_value: 0 for level_value, _label in Quiz.LEVEL_CHOICES}

    count_rows = (
        Quiz.objects.filter(test_subject__company=request.company)
        .values('test_subject_id', 'level')
        .annotate(total=Count('id'))
    )
    for row in count_rows:
        subject_key = str(row['test_subject_id'])
        level_key = row['level']
        total = row['total']
        if level_key not in question_count_map['all']:
            continue
        question_count_map['all'][level_key] += total
        if subject_key in question_count_map:
            question_count_map[subject_key][level_key] = total

    valid_levels = {value for value, _label in Quiz.LEVEL_CHOICES}
    if selected_level not in valid_levels:
        selected_level = Quiz.LEVEL_BASIC

    queryset = Quiz.objects.filter(test_subject__company=request.company, level=selected_level).select_related(
        'test_subject',
        'sub_title',
    )

    subject_label = 'all-subjects'
    if selected_subject != 'all':
        subject_id = _parse_positive_int(selected_subject)
        subject = subjects.filter(pk=subject_id).first()
        if subject:
            queryset = queryset.filter(test_subject=subject)
            subject_label = subject.subject
        else:
            errors.append('Choose a valid subject.')
            selected_subject = 'all'

    quizzes = list(queryset.order_by('test_subject__subject', 'sub_title__title', 'id'))
    if request.method == 'POST' and not errors:
        exporter = EXPORTERS.get(file_type or '')
        if not exporter:
            error_message = 'Choose a valid file type.'
            errors.append(error_message)
            messages.error(request, error_message)
        elif not quizzes:
            error_message = 'No questions found for the selected filters.'
            errors.append(error_message)
            messages.error(request, error_message)
        else:
            include_answers = answer_mode == 'with'
            payload = exporter.build(quizzes, include_answers=include_answers)
            level_label = dict(Quiz.LEVEL_CHOICES).get(selected_level, selected_level)
            answer_label = 'with-answers' if include_answers else 'without-answers'
            filename = (
                f'{slugify(subject_label) or "questions"}-'
                f'{slugify(level_label) or selected_level}-{answer_label}.{exporter.extension}'
            )
            response = HttpResponse(payload, content_type=exporter.content_type)
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response

    return render(
        request,
        'dashboard/questions_download.html',
        {
            'title': 'Source Download',
            'subjects': subjects,
            'level_choices': Quiz.LEVEL_CHOICES,
            'selected_subject': selected_subject,
            'selected_level': selected_level,
            'answer_mode': answer_mode,
            'question_count': len(quizzes),
            'question_count_map': question_count_map,
            'errors': errors,
        },
    )


@company_login_required
def candidate_list(request):
    queryset = Candidate.objects.all()
    return render_crud_list(
        request,
        queryset=queryset,
        title='Candidates',
        create_url='dashboard:candidate_create',
        edit_url_name='dashboard:candidate_update',
        delete_url_name='dashboard:candidate_delete',
        fields=['name', 'email', 'designation_tech', 'candidate_details_summary', 'created_at'],
    )


@company_login_required
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


@company_login_required
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


@company_login_required
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


@company_login_required
def attempt_list(request):
    queryset = CandidateTestAttempt.objects.filter(company=request.company).select_related('candidate', 'company')
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
            'candidate_details_json',
            'percentage',
            'is_submitted',
        ],
    )


@company_login_required
def attempt_create(request):
    form = CandidateTestAttemptForm(request.POST or None, company=request.company)
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


@company_login_required
def attempt_update(request, pk):
    attempt = get_object_or_404(CandidateTestAttempt, pk=pk, company=request.company)
    form = CandidateTestAttemptForm(request.POST or None, instance=attempt, company=request.company)
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


@company_login_required
def attempt_delete(request, pk):
    attempt = get_object_or_404(CandidateTestAttempt, pk=pk, company=request.company)
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

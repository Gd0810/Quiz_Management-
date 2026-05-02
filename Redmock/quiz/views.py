from datetime import timedelta
from decimal import Decimal

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from dashboard.models import Quiz, SubTitle, TestSubject
from dashboard.views import company_login_required

from .forms import CandidateDetailsForm
from .models import Candidate, CandidateTestAttempt

PENDING_TEST_SETUP_SESSION_KEY = 'pending_test_setup'
PENDING_SECURITY_SETUP_SESSION_KEY = 'pending_security_setup'


def _is_htmx(request):
    return request.headers.get('HX-Request') == 'true'


def _level_choices():
    return Quiz.LEVEL_CHOICES


def _parse_positive_int(raw_value, default=0):
    try:
        value = int(raw_value)
    except (TypeError, ValueError):
        return default
    return max(value, 0)


def _parse_bool(raw_value):
    if isinstance(raw_value, bool):
        return raw_value
    if raw_value is None:
        return False
    return str(raw_value).lower() in {'1', 'true', 'on', 'yes'}


def _build_security_state(company, data=None):
    data = data or {}
    has_data = bool(data)
    builder_fullscreen_available = company.allow_full_screen_lock and company.full_screen_lock
    builder_pause_available = company.allow_pause_lock and company.pause_lock
    builder_tab_guard_available = company.allow_tab_switch_guard and company.tab_switch_guard_enabled
    builder_copy_paste_available = company.allow_copy_paste_block and company.copy_paste_block_enabled
    builder_right_click_available = company.allow_right_click_disable and company.right_click_disable_enabled
    state = {
        'full_screen_lock_enabled': (
            _parse_bool(data.get('full_screen_lock_enabled')) if has_data else builder_fullscreen_available
        ),
        'pause_lock_enabled': (
            _parse_bool(data.get('pause_lock_enabled')) if has_data else builder_pause_available
        ),
        'tab_switch_guard_enabled': (
            _parse_bool(data.get('tab_switch_guard_enabled')) if has_data else builder_tab_guard_available
        ),
        'copy_paste_block_enabled': (
            _parse_bool(data.get('copy_paste_block_enabled')) if has_data else builder_copy_paste_available
        ),
        'right_click_disable_enabled': (
            _parse_bool(data.get('right_click_disable_enabled')) if has_data else builder_right_click_available
        ),
        'max_violation_warnings': _parse_positive_int(
            data.get('max_violation_warnings') if has_data else company.max_violation_warnings,
            company.max_violation_warnings or 3,
        ) or 3,
        'allow_full_screen_lock': builder_fullscreen_available,
        'allow_pause_lock': builder_pause_available,
        'allow_tab_switch_guard': builder_tab_guard_available,
        'allow_copy_paste_block': builder_copy_paste_available,
        'allow_right_click_disable': builder_right_click_available,
        'errors': [],
    }
    if not builder_fullscreen_available:
        state['full_screen_lock_enabled'] = False
    if not builder_pause_available:
        state['pause_lock_enabled'] = False
    if not builder_tab_guard_available:
        state['tab_switch_guard_enabled'] = False
    if not builder_copy_paste_available:
        state['copy_paste_block_enabled'] = False
    if not builder_right_click_available:
        state['right_click_disable_enabled'] = False
    return state


def _validate_security_state(state, company):
    if (
        state['full_screen_lock_enabled'] or state['pause_lock_enabled']
    ) and not company.exam_control_password:
        state['errors'].append(
            'Set an exam control password in dashboard security before enabling fullscreen or pause lock.'
        )
    if state['tab_switch_guard_enabled'] and state['max_violation_warnings'] <= 0:
        state['errors'].append('Max violation warnings must be greater than zero.')
    return not state['errors']


def _security_state_from_session(request, company):
    saved = request.session.get(PENDING_SECURITY_SETUP_SESSION_KEY)
    if not saved:
        return _build_security_state(company)
    state = _build_security_state(company, saved)
    state['errors'] = []
    return state


def _split_evenly(total, count):
    if count <= 0:
        return []
    base = total // count
    remainder = total % count
    return [base + (1 if index < remainder else 0) for index in range(count)]


def _subject_map(company):
    return {
        subject.id: subject
        for subject in TestSubject.objects.filter(company=company).order_by('subject')
    }


def _subtitle_map(company):
    subtitles = SubTitle.objects.filter(test_subject__company=company).select_related('test_subject').order_by('title')
    return {subtitle.id: subtitle for subtitle in subtitles}


def _available_question_counts(company, subject_ids, level_by_subject):
    counts = {}
    if not subject_ids:
        return counts

    queryset = (
        Quiz.objects.filter(test_subject__company=company, test_subject_id__in=subject_ids)
        .values('test_subject_id', 'sub_title_id', 'level')
        .order_by()
    )

    grouped = {}
    for row in queryset:
        key = (row['test_subject_id'], row['sub_title_id'], row['level'])
        grouped[key] = grouped.get(key, 0) + 1

    for (subject_id, subtitle_id, level), count in grouped.items():
        if level_by_subject.get(subject_id) == level:
            counts[(subject_id, subtitle_id)] = count

    return counts


def _build_default_allocations(question_count, subject_configs, available_counts):
    allocations = []
    if not subject_configs:
        return allocations

    subject_shares = _split_evenly(question_count, len(subject_configs))
    for index, config in enumerate(subject_configs):
        allocation_targets = config['subtitles'] or [None]
        subtitle_shares = _split_evenly(subject_shares[index], len(allocation_targets))
        for subtitle_index, subtitle in enumerate(allocation_targets):
            allocations.append(
                {
                    'subject': config['subject'],
                    'subtitle': subtitle,
                    'level': config['level'],
                    'requested_count': subtitle_shares[subtitle_index],
                    'available_count': available_counts.get(
                        (config['subject'].id, subtitle.id if subtitle else None),
                        0,
                    ),
                    'field_name': f'custom_count_{config["subject"].id}_{subtitle.id if subtitle else 0}',
                }
            )
    return allocations


def _available_questions_for_allocation(company, subject, subtitle, level):
    queryset = Quiz.objects.filter(
        test_subject__company=company,
        test_subject=subject,
        level=level,
    )
    if subtitle is None:
        queryset = queryset.filter(sub_title__isnull=True)
    else:
        queryset = queryset.filter(sub_title=subtitle)

    return [
        {
            'id': question.id,
            'label': question.question[:140],
            'has_image': bool(question.question_image),
            'updated_at': int(question.updated_at.timestamp()) if question.updated_at else 0,
        }
        for question in queryset.order_by('id')
    ]


def _build_setup_state(request, company, data=None):
    data = data or request.POST
    subject_map = _subject_map(company)
    subtitle_map = _subtitle_map(company)

    session_type = data.get('session_type') or 'single'
    custom_mode = data.get('custom_mode') == '1'
    duration_minutes = _parse_positive_int(data.get('duration_minutes'), 30) or 30
    question_count = _parse_positive_int(data.get('question_count'), 10) or 10

    selected_subject_ids = []
    level_by_subject = {}
    subtitle_ids_by_subject = {}

    if session_type == 'single':
        subject_id = _parse_positive_int(data.get('single_subject'))
        if subject_id in subject_map:
            selected_subject_ids = [subject_id]
            level_by_subject[subject_id] = data.get('single_level') or Quiz.LEVEL_BASIC
            submitted_subtitles = [
                subtitle_id
                for subtitle_id in data.getlist('single_subtitles')
                if _parse_positive_int(subtitle_id) in subtitle_map
            ]
            valid_default_ids = [
                subtitle.id for subtitle in subtitle_map.values() if subtitle.test_subject_id == subject_id
            ]
            chosen_ids = [
                _parse_positive_int(subtitle_id)
                for subtitle_id in submitted_subtitles
                if _parse_positive_int(subtitle_id) in valid_default_ids
            ]
            subtitle_ids_by_subject[subject_id] = chosen_ids or valid_default_ids
    else:
        submitted_subject_ids = [_parse_positive_int(value) for value in data.getlist('multi_subjects')]
        selected_subject_ids = [subject_id for subject_id in submitted_subject_ids if subject_id in subject_map]
        for subject_id in selected_subject_ids:
            level_by_subject[subject_id] = data.get(f'multi_level_{subject_id}') or Quiz.LEVEL_BASIC
            valid_default_ids = [
                subtitle.id for subtitle in subtitle_map.values() if subtitle.test_subject_id == subject_id
            ]
            chosen_ids = [
                _parse_positive_int(subtitle_id)
                for subtitle_id in data.getlist(f'multi_subtitles_{subject_id}')
                if _parse_positive_int(subtitle_id) in valid_default_ids
            ]
            subtitle_ids_by_subject[subject_id] = chosen_ids or valid_default_ids

    available_counts = _available_question_counts(company, selected_subject_ids, level_by_subject)

    subject_configs = []
    for subject_id in selected_subject_ids:
        subject = subject_map[subject_id]
        all_subtitles = [subtitle for subtitle in subtitle_map.values() if subtitle.test_subject_id == subject_id]
        selected_subtitle_ids = subtitle_ids_by_subject.get(subject_id, [])
        subtitles = [subtitle_map[subtitle_id] for subtitle_id in selected_subtitle_ids if subtitle_id in subtitle_map]
        subject_configs.append(
            {
                'subject': subject,
                'level': level_by_subject.get(subject_id, Quiz.LEVEL_BASIC),
                'all_subtitles': all_subtitles,
                'subtitles': subtitles,
                'selected_subtitle_ids': selected_subtitle_ids,
            }
        )

    allocations = []
    errors = []
    if selected_subject_ids:
        default_allocations = _build_default_allocations(question_count, subject_configs, available_counts)
        default_count_map = {
            allocation['field_name']: allocation['requested_count'] for allocation in default_allocations
        }
        if custom_mode:
            allocation_total = 0
            for config in subject_configs:
                allocation_targets = config['subtitles'] or [None]
                for subtitle in allocation_targets:
                    field_name = f'custom_count_{config["subject"].id}_{subtitle.id if subtitle else 0}'
                    requested_count = _parse_positive_int(
                        data.get(field_name),
                        default_count_map.get(field_name, 0),
                    )
                    available_count = available_counts.get(
                        (config['subject'].id, subtitle.id if subtitle else None),
                        0,
                    )
                    allocations.append(
                        {
                            'subject': config['subject'],
                            'subtitle': subtitle,
                            'level': config['level'],
                            'requested_count': requested_count,
                            'available_count': available_count,
                            'field_name': field_name,
                            'question_select_field': f'question_select_{config["subject"].id}_{subtitle.id if subtitle else 0}',
                            'available_questions': _available_questions_for_allocation(
                                company,
                                config['subject'],
                                subtitle,
                                config['level'],
                            ),
                            'selected_question_ids': [],
                        }
                    )
                    allocation_total += requested_count

            if allocation_total != question_count:
                errors.append(
                    f'Custom question counts must total {question_count}. Current total is {allocation_total}.'
                )
        else:
            allocations = default_allocations

    for allocation in allocations:
        if 'question_select_field' not in allocation:
            allocation['question_select_field'] = (
                f'question_select_{allocation["subject"].id}_{allocation["subtitle"].id if allocation["subtitle"] else 0}'
            )
            allocation['available_questions'] = _available_questions_for_allocation(
                company,
                allocation['subject'],
                allocation['subtitle'],
                allocation['level'],
            )
            allocation['selected_question_ids'] = []

        selected_question_ids = [
            _parse_positive_int(value)
            for value in data.getlist(allocation['question_select_field'])
            if _parse_positive_int(value)
        ]
        valid_question_ids = {question['id'] for question in allocation['available_questions']}
        allocation['selected_question_ids'] = [
            question_id for question_id in selected_question_ids if question_id in valid_question_ids
        ]

        if allocation['selected_question_ids'] and len(allocation['selected_question_ids']) != allocation['requested_count']:
            errors.append(
                f'{allocation["subject"].subject} / {(allocation["subtitle"].title if allocation["subtitle"] else "General")} '
                f'must have exactly {allocation["requested_count"]} chosen questions. '
                f'Current chosen questions: {len(allocation["selected_question_ids"])}.'
            )

    for allocation in allocations:
        if allocation['requested_count'] > allocation['available_count']:
            errors.append(
                f'{allocation["subject"].subject} / {(allocation["subtitle"].title if allocation["subtitle"] else "General")} has only '
                f'{allocation["available_count"]} questions for {allocation["level"].title()} level.'
            )

    summary_rows = []
    for config in subject_configs:
        subject_allocations = [
            allocation
            for allocation in allocations
            if allocation['subject'].id == config['subject'].id and allocation['requested_count'] > 0
        ]
        summary_rows.append(
            {
                'subject': config['subject'],
                'level': config['level'],
                'subtitles': config['subtitles'],
                'allocations': subject_allocations,
                'total_requested': sum(item['requested_count'] for item in subject_allocations),
            }
        )

    hidden_pairs = [
        {
            'subject_id': config['subject'].id,
            'level': config['level'],
            'subtitle_ids': [subtitle.id for subtitle in config['subtitles']],
        }
        for config in subject_configs
    ]

    return {
        'session_type': session_type,
        'custom_mode': custom_mode,
        'duration_minutes': duration_minutes,
        'question_count': question_count,
        'subject_map': subject_map,
        'subject_configs': subject_configs,
        'selected_subject_ids': selected_subject_ids,
        'level_by_subject': level_by_subject,
        'allocations': allocations,
        'summary_rows': summary_rows,
        'errors': errors,
        'hidden_pairs': hidden_pairs,
    }


def _validate_setup_state(state):
    if state['session_type'] == 'single' and len(state['selected_subject_ids']) != 1:
        state['errors'].append('Single session test must have exactly one subject.')
    if state['session_type'] == 'multi' and len(state['selected_subject_ids']) < 2:
        state['errors'].append('Multi session test must have at least two subjects.')
    if state['question_count'] <= 0:
        state['errors'].append('Question count must be greater than zero.')
    if state['duration_minutes'] <= 0:
        state['errors'].append('Duration minutes must be greater than zero.')
    if not state['allocations']:
        state['errors'].append('Please choose subjects and sub titles with available questions.')
    return not state['errors']


def _select_question_ids(company, allocations):
    question_ids = []
    for allocation in allocations:
        if allocation['requested_count'] <= 0:
            continue
        if allocation['selected_question_ids']:
            if len(allocation['selected_question_ids']) != allocation['requested_count']:
                raise ValueError(
                    f'{allocation["subject"].subject} / {(allocation["subtitle"].title if allocation["subtitle"] else "General")} '
                    f'must have exactly {allocation["requested_count"]} chosen questions.'
                )
            question_ids.extend(allocation['selected_question_ids'])
            continue
        queryset = Quiz.objects.filter(
            test_subject__company=company,
            test_subject=allocation['subject'],
            level=allocation['level'],
        )
        if allocation['subtitle'] is None:
            queryset = queryset.filter(sub_title__isnull=True)
        else:
            queryset = queryset.filter(sub_title=allocation['subtitle'])
        queryset = queryset.order_by('id')[: allocation['requested_count']]
        selected = list(queryset.values_list('id', flat=True))
        if len(selected) != allocation['requested_count']:
            raise ValueError(
                f'Not enough questions in {allocation["subject"].subject} / {(allocation["subtitle"].title if allocation["subtitle"] else "General")}.'
            )
        question_ids.extend(selected)
    return question_ids


def _serialize_setup(state, question_ids, security_state):
    return {
        'session_type': state['session_type'],
        'custom_mode': state['custom_mode'],
        'duration_minutes': state['duration_minutes'],
        'question_count': state['question_count'],
        'security': {
            'full_screen_lock_enabled': security_state['full_screen_lock_enabled'],
            'pause_lock_enabled': security_state['pause_lock_enabled'],
            'tab_switch_guard_enabled': security_state['tab_switch_guard_enabled'],
            'copy_paste_block_enabled': security_state['copy_paste_block_enabled'],
            'right_click_disable_enabled': security_state['right_click_disable_enabled'],
            'max_violation_warnings': security_state['max_violation_warnings'],
        },
        'selected_subjects': state['selected_subject_ids'],
        'selected_sub_titles': [
            allocation['subtitle'].id
            for allocation in state['allocations']
            if allocation['requested_count'] > 0 and allocation['subtitle'] is not None
        ],
        'allocations': [
            {
                'subject_id': allocation['subject'].id,
                'subject_name': allocation['subject'].subject,
                'subtitle_id': allocation['subtitle'].id if allocation['subtitle'] else None,
                'subtitle_name': allocation['subtitle'].title if allocation['subtitle'] else 'General',
                'level': allocation['level'],
                'requested_count': allocation['requested_count'],
                'selected_question_ids': allocation['selected_question_ids'],
            }
            for allocation in state['allocations']
            if allocation['requested_count'] > 0
        ],
        'question_ids': question_ids,
    }


def _candidate_form_context(request, company, form=None):
    pending_setup = request.session.get(PENDING_TEST_SETUP_SESSION_KEY)
    if not pending_setup:
        return redirect('quiz:start')

    if form is None:
        form = CandidateDetailsForm()

    # Build a name → svg lookup from live subjects
    from dashboard.models import TestSubject
    svg_by_name = {
        s.subject: s.subject_svg or ''
        for s in TestSubject.objects.filter(company=company).only('subject', 'subject_svg')
    }

    summary = {}
    for allocation in pending_setup['allocations']:
        key = (allocation['subject_name'], allocation['level'], svg_by_name.get(allocation['subject_name'], ''))
        summary.setdefault(key, []).append(allocation)

    security = pending_setup.get('security') or {}
    security_summary_rows = []
    if company.allow_full_screen_lock and company.full_screen_lock:
        security_summary_rows.append({
            'label': 'Fullscreen Lock',
            'value': 'On' if _parse_bool(security.get('full_screen_lock_enabled')) else 'Off',
        })
    if company.allow_pause_lock and company.pause_lock:
        security_summary_rows.append({
            'label': 'Pause Lock',
            'value': 'On' if _parse_bool(security.get('pause_lock_enabled')) else 'Off',
        })
    if company.allow_tab_switch_guard and company.tab_switch_guard_enabled:
        security_summary_rows.append({
            'label': 'Tab Switch Guard',
            'value': (
                f'{security.get("max_violation_warnings", company.max_violation_warnings or 3)} warnings'
                if _parse_bool(security.get('tab_switch_guard_enabled'))
                else 'Off'
            ),
        })
    if company.allow_copy_paste_block and company.copy_paste_block_enabled:
        security_summary_rows.append({
            'label': 'Copy / Paste Block',
            'value': 'On' if _parse_bool(security.get('copy_paste_block_enabled')) else 'Off',
        })
    if company.allow_right_click_disable and company.right_click_disable_enabled:
        security_summary_rows.append({
            'label': 'Right Click Disable',
            'value': 'On' if _parse_bool(security.get('right_click_disable_enabled')) else 'Off',
        })

    return {
        'step': 'candidate',
        'candidate_form': form,
        'pending_setup': pending_setup,
        'summary': summary,
        'security_summary_rows': security_summary_rows,
        'company': company,
    }


def _attempt_payload(attempt):
    return {
        'remaining_seconds': attempt.remaining_seconds(),
        'is_paused': attempt.is_paused,
        'current_pause_seconds': attempt.current_pause_seconds(),
        'warning_count': attempt.warning_count,
        'tab_switch_count': attempt.tab_switch_count,
    }


def _public_attempt_or_404(attempt_slug):
    return get_object_or_404(
        CandidateTestAttempt.objects.select_related('candidate', 'company'),
        public_slug=attempt_slug,
    )


def _answers_from_request(request, answer_rows):
    return [
        {
            'question_id': row['question_id'],
            'selected_answer': request.POST.get(f"question_{row['question_id']}", ''),
        }
        for row in answer_rows
    ]


def _finalize_attempt(attempt, *, question_map, updated_answers, extra_update_fields=None):
    correct_count = 0
    for row in updated_answers:
        question = question_map.get(row['question_id'])
        if question and row.get('selected_answer') == question.correct_answer:
            correct_count += 1

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
    attempt.is_paused = False
    attempt.paused_at = None

    update_fields = [
        'answers_json',
        'correct_count',
        'wrong_count',
        'percentage',
        'submitted_at',
        'is_submitted',
        'is_paused',
        'paused_at',
    ]
    if extra_update_fields:
        update_fields.extend(extra_update_fields)
    attempt.save(update_fields=list(dict.fromkeys(update_fields)))


@company_login_required
def start_test(request):
    return render(
        request,
        'quiz/start_test.html',
        {
            'step': 'security',
            'security_state': _security_state_from_session(request, request.company),
        },
    )


@company_login_required
def security_next(request):
    state = _build_security_state(request.company, request.POST)
    if not _validate_security_state(state, request.company):
        return render(
            request,
            'quiz/_builder_panel.html',
            {'step': 'security', 'security_state': state},
        )

    request.session[PENDING_SECURITY_SETUP_SESSION_KEY] = {
        'full_screen_lock_enabled': state['full_screen_lock_enabled'],
        'pause_lock_enabled': state['pause_lock_enabled'],
        'tab_switch_guard_enabled': state['tab_switch_guard_enabled'],
        'copy_paste_block_enabled': state['copy_paste_block_enabled'],
        'right_click_disable_enabled': state['right_click_disable_enabled'],
        'max_violation_warnings': state['max_violation_warnings'],
    }
    request.session.modified = True
    return render(
        request,
        'quiz/_builder_panel.html',
        {
            'step': 'setup',
            'setup_state': _build_setup_state(request, request.company),
            'level_choices': _level_choices(),
        },
    )


@company_login_required
def security_back(request):
    return render(
        request,
        'quiz/_builder_panel.html',
        {
            'step': 'security',
            'security_state': _security_state_from_session(request, request.company),
        },
    )


@company_login_required
def setup_builder(request):
    state = _build_setup_state(request, request.company)
    return render(
        request,
        'quiz/_builder_panel.html',
        {'step': 'setup', 'setup_state': state, 'level_choices': _level_choices()},
    )


@company_login_required
def setup_next(request):
    state = _build_setup_state(request, request.company)
    security_state = _security_state_from_session(request, request.company)
    if not _validate_setup_state(state):
        return render(
            request,
            'quiz/_builder_panel.html',
            {'step': 'setup', 'setup_state': state, 'level_choices': _level_choices()},
        )

    try:
        question_ids = _select_question_ids(request.company, state['allocations'])
    except ValueError as exc:
        state['errors'].append(str(exc))
        return render(
            request,
            'quiz/_builder_panel.html',
            {'step': 'setup', 'setup_state': state, 'level_choices': _level_choices()},
        )

    request.session[PENDING_TEST_SETUP_SESSION_KEY] = _serialize_setup(state, question_ids, security_state)
    request.session.modified = True
    return render(
        request,
        'quiz/_builder_panel.html',
        _candidate_form_context(request, request.company),
    )


@company_login_required
def setup_back(request):
    pending_setup = request.session.get(PENDING_TEST_SETUP_SESSION_KEY)
    post_data = request.POST.copy()

    if pending_setup:
        post_data = post_data.copy()
        post_data['session_type'] = pending_setup['session_type']
        post_data['duration_minutes'] = str(pending_setup['duration_minutes'])
        post_data['question_count'] = str(pending_setup['question_count'])
        if pending_setup.get('custom_mode'):
            post_data['custom_mode'] = '1'
        if pending_setup['session_type'] == 'single' and pending_setup['allocations']:
            first = pending_setup['allocations'][0]
            post_data['single_subject'] = str(first['subject_id'])
            post_data['single_level'] = first['level']
            for allocation in pending_setup['allocations']:
                if allocation['subtitle_id'] is not None:
                    post_data.appendlist('single_subtitles', str(allocation['subtitle_id']))
                post_data[f'custom_count_{allocation["subject_id"]}_{allocation["subtitle_id"] or 0}'] = str(allocation['requested_count'])
                for question_id in allocation.get('selected_question_ids', []):
                    post_data.appendlist(
                        f'question_select_{allocation["subject_id"]}_{allocation["subtitle_id"] or 0}',
                        str(question_id),
                    )
        else:
            for subject_id in pending_setup['selected_subjects']:
                post_data.appendlist('multi_subjects', str(subject_id))
            seen_subjects = set()
            for allocation in pending_setup['allocations']:
                if allocation['subject_id'] not in seen_subjects:
                    post_data[f'multi_level_{allocation["subject_id"]}'] = allocation['level']
                    seen_subjects.add(allocation['subject_id'])
                if allocation['subtitle_id'] is not None:
                    post_data.appendlist(f'multi_subtitles_{allocation["subject_id"]}', str(allocation['subtitle_id']))
                post_data[f'custom_count_{allocation["subject_id"]}_{allocation["subtitle_id"] or 0}'] = str(allocation['requested_count'])
                for question_id in allocation.get('selected_question_ids', []):
                    post_data.appendlist(
                        f'question_select_{allocation["subject_id"]}_{allocation["subtitle_id"] or 0}',
                        str(question_id),
                    )

    state = _build_setup_state(request, request.company, data=post_data)
    return render(
        request,
        'quiz/_builder_panel.html',
        {'step': 'setup', 'setup_state': state, 'level_choices': _level_choices()},
    )


@company_login_required
def begin_test(request):
    pending_setup = request.session.get(PENDING_TEST_SETUP_SESSION_KEY)
    if not pending_setup:
        messages.error(request, 'Test setup expired. Please configure the test again.')
        return redirect('quiz:start')

    form = CandidateDetailsForm(request.POST or None)
    if not form.is_valid():
        return render(
            request,
            'quiz/start_test.html',
            _candidate_form_context(request, request.company, form=form),
        )

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

    answers_json = [{'question_id': question_id, 'selected_answer': ''} for question_id in pending_setup['question_ids']]
    security = pending_setup.get('security') or {}
    attempt = CandidateTestAttempt.objects.create(
        candidate=candidate,
        company=request.company,
        session_type=pending_setup['session_type'],
        level=pending_setup['allocations'][0]['level'] if pending_setup['session_type'] == 'single' else 'mixed',
        question_count=len(pending_setup['question_ids']),
        duration_minutes=pending_setup['duration_minutes'],
        selected_subjects=pending_setup['selected_subjects'],
        selected_sub_titles=pending_setup['selected_sub_titles'],
        answers_json=answers_json,
        full_screen_lock_enabled=_parse_bool(
            security.get('full_screen_lock_enabled', request.company.full_screen_lock)
        ) and request.company.allow_full_screen_lock and request.company.full_screen_lock,
        pause_lock_enabled=_parse_bool(
            security.get('pause_lock_enabled', request.company.pause_lock)
        ) and request.company.allow_pause_lock and request.company.pause_lock,
        tab_switch_guard_enabled=_parse_bool(
            security.get('tab_switch_guard_enabled', request.company.tab_switch_guard_enabled)
        ) and request.company.allow_tab_switch_guard and request.company.tab_switch_guard_enabled,
        copy_paste_block_enabled=_parse_bool(
            security.get('copy_paste_block_enabled', request.company.copy_paste_block_enabled)
        ) and request.company.allow_copy_paste_block and request.company.copy_paste_block_enabled,
        right_click_disable_enabled=_parse_bool(
            security.get('right_click_disable_enabled', request.company.right_click_disable_enabled)
        ) and request.company.allow_right_click_disable and request.company.right_click_disable_enabled,
        max_violation_warnings=_parse_positive_int(
            security.get('max_violation_warnings', request.company.max_violation_warnings),
            request.company.max_violation_warnings or 3,
        ) or 3,
        started_at=timezone.now(),
    )
    request.session.pop(PENDING_TEST_SETUP_SESSION_KEY, None)
    request.session.pop(PENDING_SECURITY_SETUP_SESSION_KEY, None)
    return redirect('quiz:take', attempt_slug=attempt.public_slug)


def take_test(request, attempt_slug):
    attempt = _public_attempt_or_404(attempt_slug)
    if attempt.is_submitted:
        return redirect('quiz:result', attempt_slug=attempt.public_slug)

    answer_rows = attempt.answers_json or []
    question_ids = [row['question_id'] for row in answer_rows]
    questions = list(
        Quiz.objects.filter(id__in=question_ids, test_subject__company=attempt.company).select_related(
            'test_subject', 'sub_title'
        )
    )
    question_map = {question.id: question for question in questions}
    ordered_questions = [question_map[qid] for qid in question_ids if qid in question_map]
    question_sections = []
    section_lookup = {}

    for index, question in enumerate(ordered_questions):
        subject_name = question.test_subject.subject
        if subject_name not in section_lookup:
            section_lookup[subject_name] = {
                'subject_name': subject_name,
                'subject_svg': question.test_subject.subject_svg or '',
                'first_index': index,
                'questions': [],
            }
            question_sections.append(section_lookup[subject_name])

        section_lookup[subject_name]['questions'].append(
            {
                'index': index,
                'number': index + 1,
            }
        )

    if request.method == 'POST':
        if attempt.is_paused:
            messages.error(request, 'Resume the paused test before submitting answers.')
            return redirect('quiz:take', attempt_slug=attempt.public_slug)

        updated_answers = _answers_from_request(request, answer_rows)
        _finalize_attempt(
            attempt,
            question_map=question_map,
            updated_answers=updated_answers,
        )
        messages.success(request, 'Test submitted successfully.')
        return redirect('quiz:result', attempt_slug=attempt.public_slug)

    initial_answers = {row['question_id']: row.get('selected_answer', '') for row in answer_rows}
    context = {
        'attempt': attempt,
        'questions': ordered_questions,
        'question_sections': question_sections,
        'initial_answers': initial_answers,
        'remaining_seconds': attempt.remaining_seconds(),
        'full_screen_lock_enabled': attempt.full_screen_lock_enabled,
        'pause_lock_enabled': attempt.pause_lock_enabled,
        'tab_switch_guard_enabled': attempt.tab_switch_guard_enabled,
        'copy_paste_block_enabled': attempt.copy_paste_block_enabled,
        'right_click_disable_enabled': attempt.right_click_disable_enabled,
        'max_violation_warnings': attempt.max_violation_warnings,
        'attempt_is_paused': attempt.is_paused,
        'current_pause_seconds': attempt.current_pause_seconds(),
        'security_password_required': bool(attempt.company.exam_control_password),
        'warning_count': attempt.warning_count,
        'end_time_iso': (
            attempt.started_at + timedelta(minutes=attempt.duration_minutes)
        ).isoformat()
        if attempt.started_at
        else '',
    }
    return render(request, 'quiz/take_test.html', context)


@require_POST
def pause_attempt(request, attempt_slug):
    attempt = _public_attempt_or_404(attempt_slug)
    password = request.POST.get('password', '').strip()

    if not attempt.pause_lock_enabled:
        return JsonResponse({'ok': False, 'error': 'Pause lock is disabled for this test.'}, status=400)
    if attempt.is_submitted:
        return JsonResponse({'ok': False, 'error': 'This test is already submitted.'}, status=400)
    if not attempt.company.check_exam_control_password(password):
        return JsonResponse({'ok': False, 'error': 'Invalid exam control password.'}, status=400)
    if not attempt.is_paused:
        attempt.is_paused = True
        attempt.paused_at = timezone.now()
        attempt.save(update_fields=['is_paused', 'paused_at'])

    payload = _attempt_payload(attempt)
    payload['ok'] = True
    return JsonResponse(payload)


@require_POST
def resume_attempt(request, attempt_slug):
    attempt = _public_attempt_or_404(attempt_slug)
    password = request.POST.get('password', '').strip()

    if not attempt.pause_lock_enabled:
        return JsonResponse({'ok': False, 'error': 'Pause lock is disabled for this test.'}, status=400)
    if not attempt.company.check_exam_control_password(password):
        return JsonResponse({'ok': False, 'error': 'Invalid exam control password.'}, status=400)
    if attempt.is_paused and attempt.paused_at:
        attempt.total_paused_seconds += attempt.current_pause_seconds()
        attempt.is_paused = False
        attempt.paused_at = None
        attempt.save(update_fields=['total_paused_seconds', 'is_paused', 'paused_at'])

    payload = _attempt_payload(attempt)
    payload['ok'] = True
    return JsonResponse(payload)


@require_POST
def unlock_fullscreen(request, attempt_slug):
    attempt = _public_attempt_or_404(attempt_slug)
    password = request.POST.get('password', '').strip()

    if not attempt.full_screen_lock_enabled:
        return JsonResponse({'ok': True})
    if not attempt.company.check_exam_control_password(password):
        return JsonResponse({'ok': False, 'error': 'Invalid exam control password.'}, status=400)
    return JsonResponse({'ok': True})


@require_POST
def record_violation(request, attempt_slug):
    attempt = _public_attempt_or_404(attempt_slug)

    if attempt.is_submitted:
        return JsonResponse({'ok': True, 'already_submitted': True})

    if not attempt.tab_switch_guard_enabled:
        return JsonResponse({'ok': True, 'guard_enabled': False, 'warning_count': attempt.warning_count})

    violation_type = (request.POST.get('violation_type') or 'focus_lost').strip()[:50]
    answers = _answers_from_request(request, attempt.answers_json or [])
    violation_log = list(attempt.violation_log_json or [])
    now = timezone.now()
    violation_log.append(
        {
            'type': violation_type,
            'at': now.isoformat(),
        }
    )

    attempt.tab_switch_count += 1
    attempt.warning_count += 1
    attempt.last_violation_at = now
    attempt.violation_log_json = violation_log

    warning_limit = max(attempt.max_violation_warnings, 1)
    if attempt.warning_count >= warning_limit:
        question_ids = [row['question_id'] for row in answers]
        question_map = {
            question.id: question
            for question in Quiz.objects.filter(id__in=question_ids, test_subject__company=attempt.company)
        }
        _finalize_attempt(
            attempt,
            question_map=question_map,
            updated_answers=answers,
            extra_update_fields=[
                'tab_switch_count',
                'warning_count',
                'last_violation_at',
                'violation_log_json',
            ],
        )
        return JsonResponse(
            {
                'ok': True,
                'auto_submitted': True,
                'warning_count': attempt.warning_count,
                'redirect_url': request.build_absolute_uri(
                    redirect('quiz:result', attempt_slug=attempt.public_slug).url
                ),
            }
        )

    attempt.answers_json = answers
    attempt.save(
        update_fields=[
            'answers_json',
            'tab_switch_count',
            'warning_count',
            'last_violation_at',
            'violation_log_json',
        ]
    )
    return JsonResponse(
        {
            'ok': True,
            'auto_submitted': False,
            'warning_count': attempt.warning_count,
            'tab_switch_count': attempt.tab_switch_count,
            'warning_limit': warning_limit,
        }
    )


def test_result(request, attempt_slug):
    attempt = _public_attempt_or_404(attempt_slug)
    answer_rows = attempt.answers_json or []
    question_ids = [row['question_id'] for row in answer_rows]
    question_map = {
        question.id: question
        for question in Quiz.objects.filter(id__in=question_ids, test_subject__company=attempt.company)
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

    return render(request, 'quiz/result.html', {'attempt': attempt, 'results': results})

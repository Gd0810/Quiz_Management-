import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Redmock.settings')
django.setup()
from types import SimpleNamespace
from django.http import QueryDict
from dashboard.models import Company
from quiz.views import _build_setup_state

comp = Company.objects.first()
print('company', comp)
post = QueryDict('', mutable=True)
post.setlist('multi_subjects', ['1', '2', '3'])
post['session_type'] = 'multi'
post['custom_mode'] = '1'
post['question_count'] = '40'
post['duration_minutes'] = '60'
req = SimpleNamespace(POST=post, company=comp)
state = _build_setup_state(req, comp)
print('selected_subject_ids', state['selected_subject_ids'])
print('subject_configs len', len(state['subject_configs']))
print('summary_rows len', len(state['summary_rows']))
print('subject_config ids', [config['subject'].id for config in state['subject_configs']])
print('selected_subject_ids raw', post.getlist('multi_subjects'))

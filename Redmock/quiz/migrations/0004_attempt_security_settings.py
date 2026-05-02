from django.db import migrations, models


def copy_company_security_to_attempts(apps, schema_editor):
    CandidateTestAttempt = apps.get_model('quiz', 'CandidateTestAttempt')
    for attempt in CandidateTestAttempt.objects.select_related('company').all():
        attempt.full_screen_lock_enabled = attempt.company.full_screen_lock
        attempt.pause_lock_enabled = attempt.company.pause_lock
        attempt.tab_switch_guard_enabled = attempt.company.tab_switch_guard_enabled
        attempt.max_violation_warnings = attempt.company.max_violation_warnings
        attempt.save(
            update_fields=[
                'full_screen_lock_enabled',
                'pause_lock_enabled',
                'tab_switch_guard_enabled',
                'max_violation_warnings',
            ]
        )


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0007_company_max_violation_warnings_and_more'),
        ('quiz', '0003_candidatetestattempt_last_violation_at_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='candidatetestattempt',
            name='full_screen_lock_enabled',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='candidatetestattempt',
            name='pause_lock_enabled',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='candidatetestattempt',
            name='tab_switch_guard_enabled',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='candidatetestattempt',
            name='max_violation_warnings',
            field=models.PositiveIntegerField(default=3),
        ),
        migrations.RunPython(copy_company_security_to_attempts, migrations.RunPython.noop),
    ]

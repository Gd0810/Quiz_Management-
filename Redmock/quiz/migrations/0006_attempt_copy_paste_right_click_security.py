from django.db import migrations, models


def copy_company_browser_security_to_attempts(apps, schema_editor):
    CandidateTestAttempt = apps.get_model('quiz', 'CandidateTestAttempt')
    for attempt in CandidateTestAttempt.objects.select_related('company').all():
        attempt.copy_paste_block_enabled = (
            attempt.company.allow_copy_paste_block and attempt.company.copy_paste_block_enabled
        )
        attempt.right_click_disable_enabled = (
            attempt.company.allow_right_click_disable and attempt.company.right_click_disable_enabled
        )
        attempt.save(update_fields=['copy_paste_block_enabled', 'right_click_disable_enabled'])


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0009_company_copy_paste_right_click_security'),
        ('quiz', '0005_candidatetestattempt_public_slug'),
    ]

    operations = [
        migrations.AddField(
            model_name='candidatetestattempt',
            name='copy_paste_block_enabled',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='candidatetestattempt',
            name='right_click_disable_enabled',
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(copy_company_browser_security_to_attempts, migrations.RunPython.noop),
    ]

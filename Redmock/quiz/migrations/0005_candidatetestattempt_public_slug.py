import secrets

from django.db import migrations, models
from django.utils.text import slugify


def build_public_slug(candidate_name):
    name_slug = slugify(candidate_name) or 'candidate'
    name_slug = name_slug[:80].strip('-') or 'candidate'
    return f'{name_slug}-{secrets.token_urlsafe(12).replace("_", "").replace("-", "")[:16].lower()}'


def populate_public_slugs(apps, schema_editor):
    CandidateTestAttempt = apps.get_model('quiz', 'CandidateTestAttempt')
    for attempt in CandidateTestAttempt.objects.select_related('candidate').all():
        slug = build_public_slug(attempt.candidate.name)
        while CandidateTestAttempt.objects.filter(public_slug=slug).exclude(pk=attempt.pk).exists():
            slug = build_public_slug(attempt.candidate.name)
        attempt.public_slug = slug
        attempt.save(update_fields=['public_slug'])


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0004_attempt_security_settings'),
    ]

    operations = [
        migrations.AddField(
            model_name='candidatetestattempt',
            name='public_slug',
            field=models.CharField(blank=True, db_index=True, max_length=190, null=True, unique=True),
        ),
        migrations.RunPython(populate_public_slugs, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='candidatetestattempt',
            name='public_slug',
            field=models.CharField(blank=True, db_index=True, max_length=190, unique=True),
        ),
    ]

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0006_attempt_copy_paste_right_click_security'),
    ]

    operations = [
        migrations.AddField(
            model_name='candidatetestattempt',
            name='candidate_details_json',
            field=models.JSONField(blank=True, default=dict),
        ),
    ]

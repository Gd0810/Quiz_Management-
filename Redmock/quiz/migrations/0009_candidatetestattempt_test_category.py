from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0008_candidatetestattempt_test_link_email_sent_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='candidatetestattempt',
            name='test_category',
            field=models.CharField(
                choices=[
                    ('interview_qizze', 'Interview Qizze'),
                    ('academy_mock', 'Academy Mock'),
                    ('internship_mock', 'Internship Mock'),
                    ('general_mock', 'General Mock'),
                ],
                default='general_mock',
                max_length=30,
            ),
        ),
    ]

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0010_company_test_instructions'),
    ]

    operations = [
        migrations.CreateModel(
            name='CandidateFormField',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(max_length=120)),
                ('field_key', models.SlugField(max_length=80)),
                ('field_type', models.CharField(choices=[('text', 'Text'), ('email', 'Email'), ('phone', 'Phone'), ('number', 'Number'), ('textarea', 'Textarea'), ('select', 'Select'), ('date', 'Date'), ('checkbox', 'Checkbox')], default='text', max_length=20)),
                ('placeholder', models.CharField(blank=True, max_length=150)),
                ('help_text', models.CharField(blank=True, max_length=255)),
                ('choices_json', models.JSONField(blank=True, default=list)),
                ('required', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('sort_order', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='candidate_form_fields', to='dashboard.company')),
            ],
            options={
                'ordering': ['sort_order', 'label'],
                'unique_together': {('company', 'field_key')},
            },
        ),
    ]

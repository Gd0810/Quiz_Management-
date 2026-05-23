from django.db import migrations, models


def convert_removed_field_types(apps, schema_editor):
    CandidateFormField = apps.get_model('dashboard', 'CandidateFormField')
    CandidateFormField.objects.filter(field_type__in=['select', 'checkbox']).update(
        field_type='text',
        choices_json=[],
    )


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0011_candidateformfield'),
    ]

    operations = [
        migrations.RunPython(convert_removed_field_types, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='candidateformfield',
            name='field_type',
            field=models.CharField(choices=[('text', 'Text'), ('email', 'Email'), ('phone', 'Phone'), ('number', 'Number'), ('textarea', 'Textarea'), ('date', 'Date')], default='text', max_length=20),
        ),
    ]

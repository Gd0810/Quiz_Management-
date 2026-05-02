from django.db import migrations, models


def grant_existing_enabled_security_features(apps, schema_editor):
    Company = apps.get_model('dashboard', 'Company')
    for company in Company.objects.all():
        company.allow_full_screen_lock = company.full_screen_lock
        company.allow_pause_lock = company.pause_lock
        company.allow_tab_switch_guard = company.tab_switch_guard_enabled
        company.save(
            update_fields=[
                'allow_full_screen_lock',
                'allow_pause_lock',
                'allow_tab_switch_guard',
            ]
        )


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0007_company_max_violation_warnings_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='company',
            name='allow_full_screen_lock',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='company',
            name='allow_pause_lock',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='company',
            name='allow_tab_switch_guard',
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(grant_existing_enabled_security_features, migrations.RunPython.noop),
    ]

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0008_company_security_feature_access'),
    ]

    operations = [
        migrations.AddField(
            model_name='company',
            name='allow_copy_paste_block',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='company',
            name='allow_right_click_disable',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='company',
            name='copy_paste_block_enabled',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='company',
            name='right_click_disable_enabled',
            field=models.BooleanField(default=False),
        ),
    ]

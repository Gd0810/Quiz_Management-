from django.db import migrations, models


DEFAULT_TEST_INSTRUCTIONS = """Read each question carefully before choosing an answer. Only one option can be selected for each question.
Use Save & Next after choosing an option so you can move through the paper in order.
Questions shown in red are visited but not answered. Questions shown in blue are answered. Purple means marked for review.
You can jump to any question using the question palette on the right side at any time during the exam.
Do not refresh the browser, close the tab, or use the back button while the test is running.
The test will submit automatically when the timer reaches zero, so review unanswered questions before time ends.
Use the final Submit button only when you are sure you have completed the test."""


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0009_company_copy_paste_right_click_security'),
    ]

    operations = [
        migrations.AddField(
            model_name='company',
            name='test_instructions',
            field=models.TextField(
                blank=True,
                default=DEFAULT_TEST_INSTRUCTIONS,
                help_text='Instructions shown to candidates in the online test instructions drawer.',
            ),
        ),
    ]

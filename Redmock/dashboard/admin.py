from django.contrib import admin
from django.contrib.auth.hashers import identify_hasher, make_password
from django.core.exceptions import ValidationError
from django.contrib import messages

from .models import BulkQuestionUpload, Company, Quiz, SubTitle, TestSubject


class SubTitleInline(admin.TabularInline):
    model = SubTitle
    extra = 1


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'email',
        'is_active',
        'allow_full_screen_lock',
        'allow_pause_lock',
        'allow_tab_switch_guard',
        'full_screen_lock',
        'pause_lock',
        'tab_switch_guard_enabled',
        'max_violation_warnings',
        'created_at',
    )
    search_fields = ('name', 'email')
    list_filter = (
        'is_active',
        'allow_full_screen_lock',
        'allow_pause_lock',
        'allow_tab_switch_guard',
        'created_at',
    )
    fieldsets = (
        (
            None,
            {
                'fields': (
                    'name',
                    'image',
                    'email',
                    'password',
                    'is_active',
                )
            },
        ),
        (
            'Security Feature Access',
            {
                'fields': (
                    'allow_full_screen_lock',
                    'allow_pause_lock',
                    'allow_tab_switch_guard',
                    'exam_control_password',
                )
            },
        ),
        (
            'Company Dashboard Defaults',
            {
                'fields': (
                    'full_screen_lock',
                    'pause_lock',
                    'tab_switch_guard_enabled',
                    'max_violation_warnings',
                )
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        password = form.cleaned_data.get('password')
        exam_control_password = form.cleaned_data.get('exam_control_password')
        if not obj.allow_full_screen_lock:
            obj.full_screen_lock = False
        if not obj.allow_pause_lock:
            obj.pause_lock = False
        if not obj.allow_tab_switch_guard:
            obj.tab_switch_guard_enabled = False
        if password:
            try:
                identify_hasher(password)
            except Exception:
                obj.password = make_password(password)
        if exam_control_password:
            try:
                identify_hasher(exam_control_password)
            except Exception:
                obj.exam_control_password = make_password(exam_control_password)
        super().save_model(request, obj, form, change)


@admin.register(TestSubject)
class TestSubjectAdmin(admin.ModelAdmin):
    list_display = ('subject', 'company', 'created_at')
    list_filter = ('company',)
    search_fields = ('subject', 'company__name')
    inlines = [SubTitleInline]


@admin.register(SubTitle)
class SubTitleAdmin(admin.ModelAdmin):
    list_display = ('title', 'test_subject', 'created_at')
    list_filter = ('test_subject__company', 'test_subject')
    search_fields = ('title', 'test_subject__subject', 'test_subject__company__name')


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('question_preview', 'test_subject', 'sub_title', 'level', 'correct_answer', 'bulk_upload', 'created_at')
    list_filter = ('level', 'test_subject__company', 'test_subject')
    search_fields = ('question', 'test_subject__subject', 'sub_title__title')

    def question_preview(self, obj):
        return obj.question[:60]

    question_preview.short_description = 'Question'


@admin.register(BulkQuestionUpload)
class BulkQuestionUploadAdmin(admin.ModelAdmin):
    list_display = ('test_subject', 'sub_title', 'level', 'imported_count', 'processed_at', 'created_at')
    list_filter = ('level', 'test_subject__company', 'test_subject')
    search_fields = ('test_subject__subject', 'sub_title__title', 'notes')
    readonly_fields = ('imported_count', 'processed_at')
    actions = ('run_bulk_import',)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        try:
            imported_count = obj.import_questions()
        except ValidationError as exc:
            self.message_user(request, f'Bulk import failed: {exc}', level=messages.ERROR)
            raise
        else:
            self.message_user(
                request,
                f'Bulk import completed successfully. {imported_count} questions created.',
                level=messages.SUCCESS,
            )

    @admin.action(description='Run bulk import again for selected uploads')
    def run_bulk_import(self, request, queryset):
        imported_total = 0
        for bulk_upload in queryset:
            try:
                imported_total += bulk_upload.import_questions()
            except ValidationError as exc:
                self.message_user(
                    request,
                    f'Bulk import failed for "{bulk_upload}": {exc}',
                    level=messages.ERROR,
                )

        if imported_total:
            self.message_user(
                request,
                f'Bulk import completed. {imported_total} questions created across selected uploads.',
                level=messages.SUCCESS,
            )

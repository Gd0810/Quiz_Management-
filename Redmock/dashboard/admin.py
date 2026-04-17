from django.contrib import admin
from django.contrib.auth.hashers import identify_hasher, make_password

from .models import Company, Quiz, SubTitle, TestSubject


class SubTitleInline(admin.TabularInline):
    model = SubTitle
    extra = 1


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'is_active', 'created_at')
    search_fields = ('name', 'email')
    list_filter = ('is_active', 'created_at')

    def save_model(self, request, obj, form, change):
        password = form.cleaned_data.get('password')
        if password:
            try:
                identify_hasher(password)
            except Exception:
                obj.password = make_password(password)
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
    list_display = ('test_subject', 'sub_title', 'level', 'created_at')
    list_filter = ('level', 'test_subject__company', 'test_subject')
    search_fields = ('test_subject__subject', 'sub_title__title')

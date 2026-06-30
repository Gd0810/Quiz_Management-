from django.urls import path

from . import views

app_name = 'dashboard'

urlpatterns = [
    path('login/', views.dashboard_login, name='login'),
    path('logout/', views.dashboard_logout, name='logout'),
    path('', views.dashboard_home, name='home'),
    path('settings/instructions/', views.company_instructions, name='company_instructions'),
    path('settings/security/', views.company_settings, name='company_settings'),
    path('settings/mail/', views.company_mail_settings, name='company_mail_settings'),
    path('forms-control/', views.candidate_form_field_list, name='candidate_form_field_list'),
    path('forms-control/create/', views.candidate_form_field_create, name='candidate_form_field_create'),
    path('forms-control/<int:pk>/edit/', views.candidate_form_field_update, name='candidate_form_field_update'),
    path('forms-control/<int:pk>/delete/', views.candidate_form_field_delete, name='candidate_form_field_delete'),
    path('subjects/', views.subject_list, name='subject_list'),
    path('subjects/upload/', views.subject_question_upload, name='subject_question_upload'),
    path('subjects/create/', views.subject_create, name='subject_create'),
    path('subjects/<int:pk>/edit/', views.subject_update, name='subject_update'),
    path('subjects/<int:pk>/delete/', views.subject_delete, name='subject_delete'),
    path('quizzes/', views.quiz_list, name='quiz_list'),
    path('quizzes/source-download/', views.quiz_source_download, name='quiz_source_download'),
    path('quizzes/create/', views.quiz_create, name='quiz_create'),
    path('quizzes/<int:pk>/edit/', views.quiz_update, name='quiz_update'),
    path('quizzes/<int:pk>/delete/', views.quiz_delete, name='quiz_delete'),
    path('candidates/', views.candidate_list, name='candidate_list'),
    path('candidates/create/', views.candidate_create, name='candidate_create'),
    path('candidates/<int:pk>/edit/', views.candidate_update, name='candidate_update'),
    path('candidates/<int:pk>/delete/', views.candidate_delete, name='candidate_delete'),
    path('attempts/', views.attempt_list, name='attempt_list'),
    path('attempts/pdf/', views.attempt_pdf, name='attempt_pdf'),
    path('attempts/create/', views.attempt_create, name='attempt_create'),
    path('attempts/<int:pk>/edit/', views.attempt_update, name='attempt_update'),
    path('attempts/<int:pk>/delete/', views.attempt_delete, name='attempt_delete'),
]

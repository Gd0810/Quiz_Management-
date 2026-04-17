from django.urls import path

from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_home, name='home'),
    path('subjects/', views.subject_list, name='subject_list'),
    path('subjects/create/', views.subject_create, name='subject_create'),
    path('subjects/<int:pk>/edit/', views.subject_update, name='subject_update'),
    path('subjects/<int:pk>/delete/', views.subject_delete, name='subject_delete'),
    path('subtitles/', views.subtitle_list, name='subtitle_list'),
    path('subtitles/create/', views.subtitle_create, name='subtitle_create'),
    path('subtitles/<int:pk>/edit/', views.subtitle_update, name='subtitle_update'),
    path('subtitles/<int:pk>/delete/', views.subtitle_delete, name='subtitle_delete'),
    path('quizzes/', views.quiz_list, name='quiz_list'),
    path('quizzes/create/', views.quiz_create, name='quiz_create'),
    path('quizzes/<int:pk>/edit/', views.quiz_update, name='quiz_update'),
    path('quizzes/<int:pk>/delete/', views.quiz_delete, name='quiz_delete'),
    path('candidates/', views.candidate_list, name='candidate_list'),
    path('candidates/create/', views.candidate_create, name='candidate_create'),
    path('candidates/<int:pk>/edit/', views.candidate_update, name='candidate_update'),
    path('candidates/<int:pk>/delete/', views.candidate_delete, name='candidate_delete'),
    path('attempts/', views.attempt_list, name='attempt_list'),
    path('attempts/create/', views.attempt_create, name='attempt_create'),
    path('attempts/<int:pk>/edit/', views.attempt_update, name='attempt_update'),
    path('attempts/<int:pk>/delete/', views.attempt_delete, name='attempt_delete'),
]

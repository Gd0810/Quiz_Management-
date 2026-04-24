from django.urls import path

from . import views

app_name = 'quiz'

urlpatterns = [
    path('start/', views.start_test, name='start'),
    path('setup-builder/', views.setup_builder, name='setup_builder'),
    path('setup-next/', views.setup_next, name='setup_next'),
    path('setup-back/', views.setup_back, name='setup_back'),
    path('begin/', views.begin_test, name='begin'),
    path('attempt/<int:attempt_id>/', views.take_test, name='take'),
    path('attempt/<int:attempt_id>/pause/', views.pause_attempt, name='pause'),
    path('attempt/<int:attempt_id>/resume/', views.resume_attempt, name='resume'),
    path('attempt/<int:attempt_id>/unlock-fullscreen/', views.unlock_fullscreen, name='unlock_fullscreen'),
    path('attempt/<int:attempt_id>/result/', views.test_result, name='result'),
]

from django.urls import path

from . import views

app_name = 'quiz'

urlpatterns = [
    path('start/', views.start_test, name='start'),
    path('security-next/', views.security_next, name='security_next'),
    path('security-back/', views.security_back, name='security_back'),
    path('setup-builder/', views.setup_builder, name='setup_builder'),
    path('setup-next/', views.setup_next, name='setup_next'),
    path('setup-back/', views.setup_back, name='setup_back'),
    path('begin/', views.begin_test, name='begin'),
    path('<slug:attempt_slug>/', views.take_test, name='take'),
    path('<slug:attempt_slug>/pause/', views.pause_attempt, name='pause'),
    path('<slug:attempt_slug>/resume/', views.resume_attempt, name='resume'),
    path('<slug:attempt_slug>/unlock-fullscreen/', views.unlock_fullscreen, name='unlock_fullscreen'),
    path('<slug:attempt_slug>/record-violation/', views.record_violation, name='record_violation'),
    path('<slug:attempt_slug>/result/', views.test_result, name='result'),
]

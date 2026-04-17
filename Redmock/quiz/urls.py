from django.urls import path

from . import views

app_name = 'quiz'

urlpatterns = [
    path('start/', views.start_test, name='start'),
    path('attempt/<int:attempt_id>/', views.take_test, name='take'),
    path('attempt/<int:attempt_id>/result/', views.test_result, name='result'),
]

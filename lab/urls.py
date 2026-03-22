from django.urls import path
from . import views

urlpatterns = [
    path('', views.lab_login, name='lab-login'),
    path('login/', views.lab_login, name='lab-login-alt'),
    path('logout/', views.lab_logout, name='lab-logout'),
    path('dashboard/', views.lab_dashboard, name='lab-dashboard'),
    path('start-test/<int:pk>/', views.start_test, name='lab-start-test'),
    path('complete-test/<int:pk>/', views.complete_test, name='lab-complete-test'),
    path('upload-report/<int:pk>/', views.upload_report, name='lab-upload-report'),
    path('test-detail/<int:pk>/', views.test_detail_api, name='lab-test-detail'),
]

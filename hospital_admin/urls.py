from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static




urlpatterns = [
    path('', views.admin_login, name='admin-login'),
    path('admin-dashboard/',views.admin_dashboard, name='admin-dashboard'),
    path('hospital-admin-profile/<int:pk>/', views.hospital_admin_profile,name='hospital-admin-profile'),
    path('appointment-list',views.appointment_list, name='appointment-list'),
    path('appointment-status/<int:pk>/', views.update_appointment_status, name='admin-appointment-status'),
    path('register-doctor-list/', views.register_doctor_list,name='register-doctor-list'),
    path('pending-doctor-list/', views.pending_doctor_list,name='pending-doctor-list'),
    path('add-doctor/', views.add_doctor, name='admin-add-doctor'),
    path('edit-doctor/<int:pk>/', views.edit_doctor, name='admin-edit-doctor'),
    path('delete-doctor/<int:pk>/', views.delete_doctor, name='admin-delete-doctor'),
    path('forgot-password/', views.admin_forgot_password,name='admin_forgot_password'),
    path('hospital-list/', views.hospital_list,name='hospital-list'),
    path('add-hospital/', views.add_hospital,name='add-hospital'),
    path('edit-hospital/<int:pk>/', views.edit_hospital,name='edit-hospital'),
    path('delete-hospital/<int:pk>/', views.delete_hospital,name='delete-hospital'),
    path('hospital-list/', views.hospital_list,name='hospital-list'),
    #path('edit-hospital/', views.edit_hospital,name='edit-hospital'),
    path('invoice/',views.invoice, name='invoice'),
    path('invoice-report/',views.invoice_report, name='invoice_report'),
    path('lock-screen/', views.lock_screen,name='lock_screen'),
    path('login/',views.admin_login,name='admin_login'),
    path('patient-list/',views.patient_list, name='patient-list'),
    path('add-patient/', views.add_patient, name='admin-add-patient'),
    path('edit-patient/<int:pk>/', views.edit_patient, name='admin-edit-patient'),
    path('delete-patient/<int:pk>/', views.delete_patient, name='admin-delete-patient'),
    # path('register/', views.register,name='register'),
    path('admin_register/',views.admin_register,name='admin_register'),
    path('transactions-list/',views.transactions_list, name='transactions_list'),
    path('admin-logout/', views.logoutAdmin, name='admin-logout'),
    path('emergency/', views.emergency_details,name='emergency'),
    path('edit-emergency-information/<int:pk>/', views.edit_emergency_information,name='edit-emergency-information'),
    path('hospital-profile/', views.hospital_profile ,name='hospital-profile'),
    path('hospital-admin-profile/<int:pk>/', views.hospital_admin_profile,name='hospital-admin-profile'),
    path('create-invoice/<int:pk>/', views.create_invoice,name='create-invoice'),
    path('create-report/<int:pk>/', views.create_report,name='create-report'),
    path('add-lab-worker/', views.add_lab_worker,name='add-lab-worker'),
    path('lab-worker-list/', views.view_lab_worker,name='lab-worker-list'),
    path('edit-lab-worker/<int:pk>/', views.edit_lab_worker,name='edit-lab-worker'),
    path('delete-lab-worker/<int:pk>/', views.delete_lab_worker,name='delete-lab-worker'),
    path('department-image-list/<int:pk>', views.department_image_list,name='department-image-list'),
    path('admin-doctor-profile/<int:pk>/', views.admin_doctor_profile,name='admin-doctor-profile'),
    path('accept-doctor/<int:pk>/', views.accept_doctor,name='accept-doctor'),
    path('reject-doctor/<int:pk>/', views.reject_doctor,name='reject-doctor'),
    path('delete-department/<int:pk>',views.delete_department,name='delete-department'),
    path('edit-department/<int:pk>',views.edit_department,name='edit-department'),
    path('delete-specialization/<int:pk>/<int:pk2>/',views.delete_specialization,name='delete-specialization'),
    path('delete-service/<int:pk>/<int:pk2>/',views.delete_service,name='delete-service'),
    path('labworker-dashboard/', views.labworker_dashboard,name='labworker-dashboard'),
    path('mypatient-list/', views.mypatient_list,name='mypatient-list'),
    path('prescription-list/<int:pk>', views.prescription_list,name='prescription-list'),
    path('add-test/', views.add_test,name='add-test'),
    path('test-list/', views.test_list,name='test-list'),
    path('delete-test/<int:pk>/', views.delete_test,name='delete-test'),
    path('report-history/', views.report_history,name='report-history'),
    path('finance/', views.payment_overview, name='finance-overview'),
    path('finance/transactions/', views.transactions_list, name='transactions_list'),
    path('finance/revenue-reports/', views.revenue_reports, name='revenue-reports'),
    path('finance/revenue-report-pdf/', views.admin_revenue_report_pdf, name='admin_revenue_report_pdf'),
    
]
  


urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

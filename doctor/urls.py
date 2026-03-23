from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from .pdf import report_pdf


# from . --> same directory
# Views functions and urls must be linked. # of views == # of urls
# App URL file - urls related to hospital

urlpatterns = [
    path('', views.doctor_login, name='doctor-login'),
    path('doctor-dashboard/',views.doctor_dashboard, name='doctor-dashboard'),
    path('doctor-profile/<int:pk>/', views.doctor_profile, name='doctor-profile'),
    path('doctor-change-password/<int:pk>', views.doctor_change_password,name='doctor-change-password'),
    path('doctor-profile-settings/', views.doctor_profile_settings,name='doctor-profile-settings'),
    path('doctor-register/', views.doctor_register, name='doctor-register'),
    path('doctor-logout/', views.logoutDoctor, name='doctor-logout'),
    path('my-patients/', views.my_patients, name='my-patients'),
    path('booking/<int:pk>/', views.booking, name='booking'),
    path('booking/<int:pk>/slots/', views.booking_slots, name='booking-slots'),
    path('booking-success/', views.booking_success, name='booking-success'),
    path('schedule-timings/', views.schedule_timings, name='schedule-timings'),
    path('patient-id/', views.patient_id, name='patient-id'),
    path('create-prescription/<int:pk>/', views.create_prescription, name='create-prescription'),
    path('edit-prescription/<int:pk>/', views.edit_prescription, name='edit-prescription'),
    path('patient-profile/<int:pk>/',views.patient_profile, name='patient-profile'),
    path('delete-education/<int:pk>/',views.delete_education, name='delete-education'),
    path('delete-experience/<int:pk>/',views.delete_experience, name='delete-experience'),
    path('appointments/',views.appointments, name='appointments'),
    path('appointments/<int:pk>/add-payment/', views.add_appointment_payment, name='doctor-add-appointment-payment'),
    path('accept-appointment/<int:pk>/',views.accept_appointment, name='accept-appointment'),
    path('reject-appointment/<int:pk>/',views.reject_appointment, name='reject-appointment'),
    path('patient-search/<int:pk>/', views.patient_search, name='patient-search'),
    path('pdf/<int:pk>/',views.report_pdf, name='pdf'),
    path('doctor_review/<int:pk>/', views.doctor_review, name='doctor_review'),
    path('doctor-test-list/', views.doctor_test_list, name='doctor-test-list'),
    path('test-info/', views.test_info_lookup, name='test-info-lookup'),
    path('doctor-view-prescription/<int:pk>/', views.doctor_view_prescription, name='doctor-view-prescription'),
    path('doctor-prescription-pdf/<int:pk>/', views.doctor_prescription_pdf, name='doctor-prescription-pdf'),
    path('doctor-view-report/<int:pk>/', views.doctor_view_report, name='doctor-view-report'),
    path('doctor-lab-reports/', views.doctor_lab_reports, name='doctor-lab-reports'),

]


urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

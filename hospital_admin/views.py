import email
from email.mime import image
from multiprocessing import context
from unicodedata import name
from itertools import chain
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_control
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from hospital.models import Hospital_Information, User, Patient
from django.db.models import Q
from django.db import transaction
from django.core.paginator import Paginator
from pharmacy.models import Medicine, Pharmacist
from doctor.models import Doctor_Information, Prescription, Prescription_test, Report, Appointment, Experience , Education,Specimen,Test
from pharmacy.models import Order, Cart
from sslcommerz.models import Payment
from .forms import (
    AdminUserCreationForm,
    LabWorkerCreationForm,
    EditHospitalForm,
    EditEmergencyForm,
    AdminForm,
    PharmacistCreationForm,
    DoctorAccountCreationForm,
    DoctorAdminUpdateForm,
    LabWorkerAdminCreationForm,
    LabWorkerAdminUpdateForm,
    PatientAdminCreationForm,
    PatientAdminUpdateForm,
)

from .models import Admin_Information,specialization,service,hospital_department, Clinical_Laboratory_Technician, Test_Information
import random,re
import string
from django.db.models import  Count
from datetime import datetime
import datetime
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseForbidden

from django.core.mail import BadHeaderError, send_mail
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.utils.html import strip_tags
from .utils import searchMedicines, generate_secure_password, generate_unique_user_id, send_account_credentials_email

# Create your views here.

@csrf_exempt
@login_required(login_url='admin_login')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def admin_dashboard(request):
    # admin = Admin_Information.objects.get(user_id=pk)
    if request.user.is_hospital_admin:
        user = Admin_Information.objects.get(user=request.user)
        total_patient_count = Patient.objects.count()
        total_doctor_count = Doctor_Information.objects.count()
        total_hospital_count = Hospital_Information.objects.count()
        total_labworker_count = Clinical_Laboratory_Technician.objects.count()
        total_appointment_count = Appointment.objects.count()
        pending_appointment = Appointment.objects.filter(appointment_status='pending').count()
        doctors = Doctor_Information.objects.select_related('hospital_name', 'specialization').order_by('-doctor_id')[:5]
        patients = Patient.objects.order_by('-patient_id')[:5]
        hospitals = Hospital_Information.objects.order_by('-hospital_id')[:5]
        lab_workers = Clinical_Laboratory_Technician.objects.select_related('hospital').order_by('-technician_id')[:5]
        
        sat_date = datetime.date.today()
        sat_date_str = str(sat_date)
        sat = sat_date.strftime("%A")

        sun_date = sat_date + datetime.timedelta(days=1) 
        sun_date_str = str(sun_date)
        sun = sun_date.strftime("%A")
        
        mon_date = sat_date + datetime.timedelta(days=2) 
        mon_date_str = str(mon_date)
        mon = mon_date.strftime("%A")
        
        tues_date = sat_date + datetime.timedelta(days=3) 
        tues_date_str = str(tues_date)
        tues = tues_date.strftime("%A")
        
        wed_date = sat_date + datetime.timedelta(days=4) 
        wed_date_str = str(wed_date)
        wed = wed_date.strftime("%A")
        
        thurs_date = sat_date + datetime.timedelta(days=5) 
        thurs_date_str = str(thurs_date)
        thurs = thurs_date.strftime("%A")
        
        fri_date = sat_date + datetime.timedelta(days=6) 
        fri_date_str = str(fri_date)
        fri = fri_date.strftime("%A")
        
        sat_count = Appointment.objects.filter(date=sat_date_str).filter(Q(appointment_status='pending') | Q(appointment_status='confirmed')).count()
        sun_count = Appointment.objects.filter(date=sun_date_str).filter(Q(appointment_status='pending') | Q(appointment_status='confirmed')).count()
        mon_count = Appointment.objects.filter(date=mon_date_str).filter(Q(appointment_status='pending') | Q(appointment_status='confirmed')).count()
        tues_count = Appointment.objects.filter(date=tues_date_str).filter(Q(appointment_status='pending') | Q(appointment_status='confirmed')).count()
        wed_count = Appointment.objects.filter(date=wed_date_str).filter(Q(appointment_status='pending') | Q(appointment_status='confirmed')).count()
        thurs_count = Appointment.objects.filter(date=thurs_date_str).filter(Q(appointment_status='pending') | Q(appointment_status='confirmed')).count()
        fri_count = Appointment.objects.filter(date=fri_date_str).filter(Q(appointment_status='pending') | Q(appointment_status='confirmed')).count()

        recent_activity = []
        for item in chain(doctors, patients, lab_workers, Appointment.objects.select_related('doctor', 'patient').order_by('-id')[:8]):
            if isinstance(item, Doctor_Information):
                recent_activity.append({'sort_key': item.doctor_id, 'icon': 'user-md', 'title': item.name or item.username, 'subtitle': 'Doctor added', 'badge': 'Doctor'})
            elif isinstance(item, Patient):
                recent_activity.append({'sort_key': item.patient_id, 'icon': 'user-injured', 'title': item.name or item.username, 'subtitle': 'Patient added', 'badge': 'Patient'})
            elif isinstance(item, Clinical_Laboratory_Technician):
                recent_activity.append({'sort_key': item.technician_id, 'icon': 'flask', 'title': item.name or item.username, 'subtitle': 'Lab technologist added', 'badge': 'Lab'})
            elif isinstance(item, Appointment):
                recent_activity.append({'sort_key': item.id, 'icon': 'calendar-check', 'title': f"{getattr(item.patient, 'name', 'Patient')} with {getattr(item.doctor, 'name', 'Doctor')}", 'subtitle': f"Appointment {item.appointment_status}", 'badge': 'Appointment'})

        recent_activity = sorted(recent_activity, key=lambda entry: entry['sort_key'], reverse=True)[:8]

        # ── Financial summary for dashboard ──────────────────────────────────
        _dash_today      = datetime.date.today()
        _dash_month_str  = _dash_today.strftime('%Y-%m')
        _dash_valid      = list(Payment.objects.filter(status='VALID').all())

        def _ds(p):
            try:
                return float(p.currency_amount or 0)
            except (ValueError, TypeError):
                return 0.0

        dash_total_revenue   = round(sum(_ds(p) for p in _dash_valid), 2)
        dash_today_revenue   = round(sum(_ds(p) for p in _dash_valid
                                         if p.transaction_date and str(p.transaction_date).startswith(str(_dash_today))), 2)
        dash_monthly_revenue = round(sum(_ds(p) for p in _dash_valid
                                         if p.transaction_date and str(p.transaction_date).startswith(_dash_month_str)), 2)
        dash_recent_payments = sorted(_dash_valid, key=lambda p: p.payment_id, reverse=True)[:5]

        # Last 6 months revenue for mini-chart
        _dash_monthly = {}
        for p in _dash_valid:
            if p.transaction_date:
                m = str(p.transaction_date)[:7]
                if len(m) == 7 and '-' in m:
                    _dash_monthly[m] = _dash_monthly.get(m, 0) + _ds(p)
        _dash_sorted = sorted(_dash_monthly.keys())[-6:]
        dash_rev_labels = [m for m in _dash_sorted]
        dash_rev_data   = [round(_dash_monthly.get(m, 0), 2) for m in _dash_sorted]
        # ─────────────────────────────────────────────────────────────────────

        context = {
            'admin': user,
            'total_patient_count': total_patient_count,
            'total_doctor_count': total_doctor_count,
            'total_hospital_count': total_hospital_count,
            'total_labworker_count': total_labworker_count,
            'total_appointment_count': total_appointment_count,
            'pending_appointment': pending_appointment,
            'doctors': doctors,
            'patients': patients,
            'hospitals': hospitals,
            'lab_workers': lab_workers,
            'sat_count': sat_count,
            'sun_count': sun_count,
            'mon_count': mon_count,
            'tues_count': tues_count,
            'wed_count': wed_count,
            'thurs_count': thurs_count,
            'fri_count': fri_count,
            'sat': sat,
            'sun': sun,
            'mon': mon,
            'tues': tues,
            'wed': wed,
            'thurs': thurs,
            'fri': fri,
            'chart_labels': [sat, sun, mon, tues, wed, thurs, fri],
            'chart_counts': [sat_count, sun_count, mon_count, tues_count, wed_count, thurs_count, fri_count],
            'recent_activity': recent_activity,
            'quick_actions': [
                {'label': 'Add Doctor', 'url_name': 'admin-add-doctor', 'icon': 'user-md'},
                {'label': 'Add Patient', 'url_name': 'admin-add-patient', 'icon': 'user-plus'},
                {'label': 'Add Lab Technologist', 'url_name': 'add-lab-worker', 'icon': 'flask'},
                {'label': 'Manage Appointments', 'url_name': 'appointment-list', 'icon': 'calendar-check'},
            ],
            # Financial
            'dash_total_revenue':   dash_total_revenue,
            'dash_today_revenue':   dash_today_revenue,
            'dash_monthly_revenue': dash_monthly_revenue,
            'dash_recent_payments': dash_recent_payments,
            'dash_rev_labels':      dash_rev_labels,
            'dash_rev_data':        dash_rev_data,
        }
        return render(request, 'hospital_admin/admin-dashboard.html', context)
    elif request.user.is_labworker:
        # messages.error(request, 'You are not authorized to access this page')
        return redirect('labworker-dashboard')
    # return render(request, 'hospital_admin/admin-dashboard.html', context)

@csrf_exempt
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def logoutAdmin(request):
    logout(request)
    messages.error(request, 'User Logged out')
    return redirect('admin_login')
            
@csrf_exempt
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def admin_login(request):
    if request.method == 'GET':
        return render(request, 'hospital_admin/login.html')
    elif request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        try:
            user = User.objects.get(username=username)
        except:
            messages.error(request, 'Username does not exist')

        user = authenticate(username=username, password=password)

        if user is not None:
            login(request, user)
            if user.is_hospital_admin:
                messages.success(request, 'User logged in')
                return redirect('admin-dashboard')
            elif user.is_labworker:
                messages.success(request, 'User logged in')
                return redirect('lab-dashboard')
            elif user.is_pharmacist:
                messages.success(request, 'User logged in')
                return redirect('pharmacist-dashboard')
            else:
                return redirect('admin-logout')
        else:
            messages.error(request, 'Invalid username or password')
        

    return render(request, 'hospital_admin/login.html')


@csrf_exempt
def admin_register(request):
    # Security: hospital admin accounts must be created by Django Super Admin only.
    # This prevents public self-registration of admin accounts.
    if not request.user.is_authenticated or not getattr(request.user, 'is_superuser', False):
        messages.error(request, 'Only the Super Admin can create hospital admin accounts.')
        return redirect('admin_login')

    page = 'hospital_admin/register'
    form = AdminUserCreationForm()

    if request.method == 'POST':
        form = AdminUserCreationForm(request.POST)
        if form.is_valid():
            # form.save()
            # commit=False --> don't save to database yet (we have a chance to modify object)
            user = form.save(commit=False)
            user.is_hospital_admin = True
            user.save()

            messages.success(request, 'User account was created!')
            
            # After user is created, we can log them in
            #login(request, user)
            return redirect('admin_login')

        else:
            messages.error(request, 'An error has occurred during registration')

    context = {'page': page, 'form': form}
    return render(request, 'hospital_admin/register.html', context)

@csrf_exempt
@login_required(login_url='admin_login')
def admin_forgot_password(request):
    return render(request, 'hospital_admin/forgot-password.html')

@csrf_exempt
@login_required(login_url='admin_login')
def invoice(request):
    return render(request, 'hospital_admin/invoice.html')

@csrf_exempt
@login_required(login_url='admin_login')
def invoice_report(request):
    return render(request, 'hospital_admin/invoice-report.html')

@login_required(login_url='admin_login')
def lock_screen(request):
    return render(request, 'hospital_admin/lock-screen.html')

@csrf_exempt
@login_required(login_url='admin_login')
def patient_list(request):
    if request.user.is_hospital_admin:
        user = Admin_Information.objects.get(user=request.user)
    search_query = (request.GET.get('q') or '').strip()
    patients = Patient.objects.all().order_by('-patient_id')
    if search_query:
        patients = patients.filter(
            Q(name__icontains=search_query)
            | Q(username__icontains=search_query)
            | Q(email__icontains=search_query)
            | Q(phone_number__icontains=search_query)
        )

    paginator = Paginator(patients, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'hospital_admin/patient-list.html', {'all': page_obj.object_list, 'page_obj': page_obj, 'admin': user, 'search_query': search_query})

@csrf_exempt
@login_required(login_url='admin_login')
def specialitites(request):
    return render(request, 'hospital_admin/specialities.html')

@csrf_exempt
@login_required(login_url='admin_login')
def appointment_list(request):
    if not request.user.is_hospital_admin:
        return redirect('admin-logout')

    admin = Admin_Information.objects.get(user=request.user)
    search_query = (request.GET.get('q') or '').strip()
    status_filter = (request.GET.get('status') or '').strip()
    appointments = Appointment.objects.select_related('doctor', 'patient').order_by('-id')
    if search_query:
        appointments = appointments.filter(
            Q(patient__name__icontains=search_query)
            | Q(doctor__name__icontains=search_query)
            | Q(serial_number__icontains=search_query)
            | Q(transaction_id__icontains=search_query)
        )
    if status_filter:
        appointments = appointments.filter(appointment_status=status_filter)

    paginator = Paginator(appointments, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'hospital_admin/appointment-list.html', {
        'admin': admin,
        'appointments': page_obj.object_list,
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'status_choices': Appointment.APPOINTMENT_STATUS,
    })

@login_required(login_url='admin_login')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def transactions_list(request):
    if not request.user.is_hospital_admin:
        return redirect('admin-logout')
    admin = Admin_Information.objects.get(user=request.user)

    payments = Payment.objects.select_related(
        'patient', 'appointment', 'appointment__doctor'
    ).order_by('-payment_id')

    search_q = (request.GET.get('q') or '').strip()
    status_f = (request.GET.get('status') or '').strip()
    ptype_f  = (request.GET.get('ptype') or '').strip()

    if search_q:
        payments = payments.filter(
            Q(name__icontains=search_q) |
            Q(transaction_id__icontains=search_q) |
            Q(invoice_number__icontains=search_q) |
            Q(patient__name__icontains=search_q)
        )
    if status_f:
        payments = payments.filter(status=status_f)
    if ptype_f:
        payments = payments.filter(payment_type=ptype_f)

    def _safe(p):
        try:
            return float(p.currency_amount or 0)
        except (ValueError, TypeError):
            return 0.0

    all_payments   = list(Payment.objects.all())
    valid_payments = [p for p in all_payments if p.status == 'VALID']
    total_revenue  = sum(_safe(p) for p in valid_payments)

    paginator = Paginator(payments, 15)
    page_obj  = paginator.get_page(request.GET.get('page'))

    context = {
        'admin': admin,
        'payments': page_obj.object_list,
        'page_obj': page_obj,
        'search_query': search_q,
        'status_filter': status_f,
        'ptype_filter': ptype_f,
        'total_revenue': round(total_revenue, 2),
        'total_transactions': len(all_payments),
        'paid_count': len(valid_payments),
        'failed_count': sum(1 for p in all_payments if p.status not in ('VALID', 'VALIDATED', None, '')),
    }
    return render(request, 'hospital_admin/transactions-list.html', context)

@csrf_exempt
@login_required(login_url='admin_login')
def emergency_details(request):
    user = Admin_Information.objects.get(user=request.user)
    hospitals = Hospital_Information.objects.all()
    context = { 'admin': user, 'all': hospitals}
    return render(request, 'hospital_admin/emergency.html', context)

@csrf_exempt
@login_required(login_url='admin_login')
def hospital_list(request):
    user = Admin_Information.objects.get(user=request.user)
    hospitals = Hospital_Information.objects.all()
    context = { 'admin': user, 'hospitals': hospitals}
    return render(request, 'hospital_admin/hospital-list.html', context)

@csrf_exempt
@login_required(login_url='admin_login')
def appointment_list(request):
    if not request.user.is_hospital_admin:
        return redirect('admin-logout')

    admin = Admin_Information.objects.get(user=request.user)
    search_query = (request.GET.get('q') or '').strip()
    status_filter = (request.GET.get('status') or '').strip()
    appointments = Appointment.objects.select_related('doctor', 'patient').order_by('-id')
    if search_query:
        appointments = appointments.filter(
            Q(patient__name__icontains=search_query)
            | Q(doctor__name__icontains=search_query)
            | Q(serial_number__icontains=search_query)
            | Q(transaction_id__icontains=search_query)
        )
    if status_filter:
        appointments = appointments.filter(appointment_status=status_filter)

    paginator = Paginator(appointments, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'hospital_admin/appointment-list.html', {
        'admin': admin,
        'appointments': page_obj.object_list,
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'status_choices': Appointment.APPOINTMENT_STATUS,
    })

@csrf_exempt
@login_required(login_url='admin_login')
def hospital_profile(request):
    return render(request, 'hospital-profile.html')

@csrf_exempt
@login_required(login_url='admin_login')
def hospital_admin_profile(request, pk):

    # profile = request.user.profile
    # get user id of logged in user, and get all info from table
    admin = Admin_Information.objects.get(user_id=pk)
    form = AdminForm(instance=admin)

    if request.method == 'POST':
        form = AdminForm(request.POST, request.FILES,
                          instance=admin)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile Updated')
            return redirect('admin-dashboard', pk=pk)
        else:
            form = AdminForm()

    context = {'admin': admin, 'form': form}
    return render(request, 'hospital_admin/hospital-admin-profile.html', context)

@csrf_exempt
@login_required(login_url='admin_login')
def add_hospital(request):
    if  request.user.is_hospital_admin:
        user = Admin_Information.objects.get(user=request.user)

        if request.method == 'POST':
            hospital = Hospital_Information()
            
            if 'featured_image' in request.FILES:
                featured_image = request.FILES['featured_image']
            else:
                featured_image = "departments/default.png"
            
            hospital_name = request.POST.get('hospital_name')
            address = request.POST.get('address')
            description = request.POST.get('description')
            email = request.POST.get('email')
            phone_number = request.POST.get('phone_number') 
            hospital_type = request.POST.get('type')
            specialization_name = request.POST.getlist('specialization')
            department_name = request.POST.getlist('department')
            service_name = request.POST.getlist('service')
            
        
            hospital.name = hospital_name
            hospital.description = description
            hospital.address = address
            hospital.email = email
            hospital.phone_number =phone_number
            hospital.featured_image=featured_image 
            hospital.hospital_type=hospital_type
            
            # print(department_name[0])
         
            hospital.save()
            
            for i in range(len(department_name)):
                departments = hospital_department(hospital=hospital)
                # print(department_name[i])
                departments.hospital_department_name = department_name[i]
                departments.save()
                
            for i in range(len(specialization_name)):
                specializations = specialization(hospital=hospital)
                specializations.specialization_name=specialization_name[i]
                specializations.save()
                
            for i in range(len(service_name)):
                services = service(hospital=hospital)
                services.service_name = service_name[i]
                services.save()
            
            messages.success(request, 'Hospital Added')
            return redirect('hospital-list')

        context = { 'admin': user}
        return render(request, 'hospital_admin/add-hospital.html',context)


# def edit_hospital(request, pk):
#     hospital = Hospital_Information.objects.get(hospital_id=pk)
#     return render(request, 'hospital_admin/edit-hospital.html')

@csrf_exempt
@login_required(login_url='admin_login')
def edit_hospital(request, pk):
    if  request.user.is_hospital_admin:
        user = Admin_Information.objects.get(user=request.user)
        hospital = Hospital_Information.objects.get(hospital_id=pk)
        old_featured_image = hospital.featured_image

        if request.method == 'GET':
            specializations = specialization.objects.filter(hospital=hospital)
            services = service.objects.filter(hospital=hospital)
            departments = hospital_department.objects.filter(hospital=hospital)
            context = {'hospital': hospital, 'specializations': specializations, 'services': services,'departments':departments, 'admin': user}
            return render(request, 'hospital_admin/edit-hospital.html',context)

        elif request.method == 'POST':
            if 'featured_image' in request.FILES:
                featured_image = request.FILES['featured_image']
            else:
                featured_image = old_featured_image
                               
            hospital_name = request.POST.get('hospital_name')
            address = request.POST.get('address')
            description = request.POST.get('description')
            email = request.POST.get('email')
            phone_number = request.POST.get('phone_number') 
            hospital_type = request.POST.get('type')
            
            specialization_name = request.POST.getlist('specialization')
            department_name = request.POST.getlist('department')
            service_name = request.POST.getlist('service')

            hospital.name = hospital_name
            hospital.description = description
            hospital.address = address
            hospital.email = email
            hospital.phone_number =phone_number
            hospital.featured_image =featured_image 
            hospital.hospital_type =hospital_type
            
            # specializations.specialization_name=specialization_name
            # services.service_name = service_name
            # departments.hospital_department_name = department_name 

            hospital.save()

            # Specialization
            for i in range(len(specialization_name)):
                specializations = specialization(hospital=hospital)
                specializations.specialization_name = specialization_name[i]
                specializations.save()

            # Experience
            for i in range(len(service_name)):
                services = service(hospital=hospital)
                services.service_name = service_name[i]
                services.save()
                
            for i in range(len(department_name)):
                departments = hospital_department(hospital=hospital)
                departments.hospital_department_name = department_name[i]
                departments.save()

            messages.success(request, 'Hospital Updated')
            return redirect('hospital-list')

@csrf_exempt
@login_required(login_url='admin_login')
def delete_specialization(request, pk, pk2):
    specializations = specialization.objects.get(specialization_id=pk)
    specializations.delete()
    messages.success(request, 'Delete Specialization')
    return redirect('edit-hospital', pk2)

@csrf_exempt
@login_required(login_url='admin_login')
def delete_service(request, pk, pk2):
    services = service.objects.get(service_id=pk)
    services.delete()
    messages.success(request, 'Delete Service')
    return redirect('edit-hospital', pk2)

@csrf_exempt
@login_required(login_url='admin_login')
def edit_emergency_information(request, pk):

    hospital = Hospital_Information.objects.get(hospital_id=pk)
    form = EditEmergencyForm(instance=hospital)  

    if request.method == 'POST':
        form = EditEmergencyForm(request.POST, request.FILES,
                           instance=hospital)  
        if form.is_valid():
            form.save()
            messages.success(request, 'Emergency information added')
            return redirect('emergency')
        else:
            form = EditEmergencyForm()

    context = {'hospital': hospital, 'form': form}
    return render(request, 'hospital_admin/edit-emergency-information.html', context)

@csrf_exempt
@login_required(login_url='admin_login')
def delete_hospital(request, pk):
	hospital = Hospital_Information.objects.get(hospital_id=pk)
	hospital.delete()
	return redirect('hospital-list')


@login_required(login_url='admin_login')
def generate_random_invoice():
    N = 4
    string_var = ""
    string_var = ''.join(random.choices(string.digits, k=N))
    string_var = "#INV-" + string_var
    return string_var

@csrf_exempt
@login_required(login_url='admin_login')
def create_invoice(request, pk):
    if  request.user.is_hospital_admin:
        user = Admin_Information.objects.get(user=request.user)

    patient = Patient.objects.get(patient_id=pk)

    if request.method == 'POST':
        invoice = Payment(patient=patient)
        
        consulation_fee = request.POST['consulation_fee']
        report_fee = request.POST['report_fee']
        #total_ammount = request.POST['currency_amount']
        invoice.currency_amount = int(consulation_fee) + int(report_fee)
        invoice.consulation_fee = consulation_fee
        invoice.report_fee = report_fee
        invoice.invoice_number = generate_random_invoice()
        invoice.name = patient
        invoice.status = 'Pending'
    
        invoice.save()
        return redirect('patient-list')

    context = {'patient': patient,'admin': user}
    return render(request, 'hospital_admin/create-invoice.html', context)


@login_required(login_url='admin_login')
def generate_random_specimen():
    N = 4
    string_var = ""
    string_var = ''.join(random.choices(string.digits, k=N))
    string_var = "#INV-" + string_var
    return string_var

@login_required(login_url='admin-login')
@csrf_exempt
def create_report(request, pk):
    if request.user.is_labworker:
        lab_workers = Clinical_Laboratory_Technician.objects.get(user=request.user)
        prescription =Prescription.objects.get(prescription_id=pk)
        patient = Patient.objects.get(patient_id=prescription.patient_id)
        doctor = Doctor_Information.objects.get(doctor_id=prescription.doctor_id)
        tests = Prescription_test.objects.filter(prescription=prescription).filter(test_info_pay_status='Paid')
        

        if request.method == 'POST':
            report = Report(doctor=doctor, patient=patient)
            
            specimen_type = request.POST.getlist('specimen_type')
            collection_date  = request.POST.getlist('collection_date')
            receiving_date = request.POST.getlist('receiving_date')
            test_name = request.POST.getlist('test_name')
            result = request.POST.getlist('result')
            unit = request.POST.getlist('unit')
            referred_value = request.POST.getlist('referred_value')
            delivery_date = request.POST.get('delivery_date')
            other_information= request.POST.get('other_information')

            # # Save to report table
            # report.test_name = test_name
            # report.result = result
            report.delivery_date = delivery_date
            report.other_information = other_information
            # #report.specimen_id =generate_random_specimen()
            # report.specimen_type = specimen_type
            # report.collection_date  = collection_date 
            # report.receiving_date = receiving_date
            # report.unit = unit
            # report.referred_value = referred_value

            report.save()

            for i in range(len(specimen_type)):
                specimens = Specimen(report=report)
                specimens.specimen_type = specimen_type[i]
                specimens.collection_date = collection_date[i]
                specimens.receiving_date = receiving_date[i]
                specimens.save()
                
            for i in range(len(test_name)):
                tests = Test(report=report)
                tests.test_name=test_name[i]
                tests.result=result[i]
                tests.unit=unit[i]
                tests.referred_value=referred_value[i]
                tests.save()
            
            # mail
            doctor_name = doctor.name
            doctor_email = doctor.email
            patient_name = patient.name
            patient_email = patient.email
            report_id = report.report_id
            delivery_date = report.delivery_date
            
            subject = "Report Delivery"

            values = {
                    "doctor_name":doctor_name,
                    "doctor_email":doctor_email,
                    "patient_name":patient_name,
                    "report_id":report_id,
                    "delivery_date":delivery_date,
                }

            html_message = render_to_string('hospital_admin/report-mail-delivery.html', {'values': values})
            plain_message = strip_tags(html_message)

            try:
                send_mail(subject, plain_message, 'hospital_admin@gmail.com',  [patient_email], html_message=html_message, fail_silently=False)
            except BadHeaderError:
                return HttpResponse('Invalid header found') 

            return redirect('mypatient-list')

        context = {'prescription':prescription,'lab_workers':lab_workers,'tests':tests}
        return render(request, 'hospital_admin/create-report.html',context)

@csrf_exempt
@login_required(login_url='admin_login')
def add_pharmacist(request):
    if request.user.is_hospital_admin:
        user = Admin_Information.objects.get(user=request.user)
        form = PharmacistCreationForm()
     
        if request.method == 'POST':
            form = PharmacistCreationForm(request.POST)
            if form.is_valid():
                # form.save(), commit=False --> don't save to database yet (we have a chance to modify object)
                user = form.save(commit=False)
                user.is_pharmacist = True
                user.save()

                messages.success(request, 'Pharmacist account was created!')

                # After user is created, we can log them in
                #login(request, user)
                return redirect('pharmacist-list')
            else:
                messages.error(request, 'An error has occurred during registration')
    
    context = {'form': form, 'admin': user}
    return render(request, 'hospital_admin/add-pharmacist.html', context)
  
@csrf_exempt
@login_required(login_url='admin_login')
def medicine_list(request):
    if request.user.is_authenticated:
        if request.user.is_pharmacist:
            pharmacist = Pharmacist.objects.get(user=request.user)
            medicine = Medicine.objects.all()
            orders = Order.objects.filter(user=request.user, ordered=False)
            carts = Cart.objects.filter(user=request.user, purchased=False)
            
            medicine, search_query = searchMedicines(request)
            
            if carts.exists() and orders.exists():
                order = orders[0]
                context = {'medicine':medicine,
                        'pharmacist':pharmacist,
                        'search_query': search_query,
                        'order': order,
                        'carts': carts,}
                return render(request, 'hospital_admin/medicine-list.html',context)
            else:
                context = {'medicine':medicine,
                            'pharmacist':pharmacist,
                            'search_query': search_query,
                            'orders': orders,
                            'carts': carts,}
                return render(request, 'hospital_admin/medicine-list.html',context)
                

@login_required(login_url='admin_login')
def generate_random_medicine_ID():
    N = 4
    string_var = ""
    string_var = ''.join(random.choices(string.digits, k=N))
    string_var = "#M-" + string_var
    return string_var

@csrf_exempt
@login_required(login_url='admin_login')
def add_medicine(request):
    if request.user.is_pharmacist:
     user = Pharmacist.objects.get(user=request.user)
     
    if request.method == 'POST':
       medicine = Medicine()
       
       if 'featured_image' in request.FILES:
           featured_image = request.FILES['featured_image']
       else:
           featured_image = "medicines/default.png"
       
       name = request.POST.get('name')
       Prescription_reqiuired = request.POST.get('requirement_type')     
       weight = request.POST.get('weight') 
       quantity = request.POST.get('quantity')
       medicine_category = request.POST.get('category_type')
       medicine_type = request.POST.get('medicine_type')
       description = request.POST.get('description')
       price = request.POST.get('price')
       
       medicine.name = name
       medicine.Prescription_reqiuired = Prescription_reqiuired
       medicine.weight = weight
       medicine.quantity = quantity
       medicine.medicine_category = medicine_category
       medicine.medicine_type = medicine_type
       medicine.description = description
       medicine.price = price
       medicine.featured_image = featured_image
       medicine.stock_quantity = 80
       #medicine.medicine_id = generate_random_medicine_ID()
       
       medicine.save()
       
       return redirect('medicine-list')
   
    return render(request, 'hospital_admin/add-medicine.html',{'admin': user})

@csrf_exempt
@login_required(login_url='admin_login')
def edit_medicine(request, pk):
    if request.user.is_pharmacist:
        user = Pharmacist.objects.get(user=request.user)
        
        medicine = Medicine.objects.get(serial_number=pk)
        old_medicine_image = medicine.featured_image
        
        if request.method == 'POST':
            if 'featured_image' in request.FILES:
                featured_image = request.FILES['featured_image']
            else:
                featured_image = old_medicine_image
                name = request.POST.get('name')
                Prescription_reqiuired = request.POST.get('requirement_type')     
                weight = request.POST.get('weight') 
                quantity = request.POST.get('quantity')
                medicine_category = request.POST.get('category_type')
                medicine_type = request.POST.get('medicine_type')
                description = request.POST.get('description')
                price = request.POST.get('price')
                
                medicine.name = name
                medicine.Prescription_reqiuired = Prescription_reqiuired
                medicine.weight = weight
                medicine.quantity = quantity
                medicine.medicine_category = medicine_category
                medicine.medicine_type = medicine_type
                medicine.description = description
                medicine.price = price
                medicine.featured_image = featured_image
                medicine.stock_quantity = 80
                #medicine.medicine_id = generate_random_medicine_ID()
            
                medicine.save()
            
                return redirect('medicine-list')
   
    return render(request, 'hospital_admin/edit-medicine.html',{'medicine': medicine,'admin': user})


@csrf_exempt
@login_required(login_url='admin_login')
def delete_medicine(request, pk):
    if request.user.is_pharmacist:
        user = Pharmacist.objects.get(user=request.user)
        medicine = Medicine.objects.get(serial_number=pk)
        medicine.delete()
        return redirect('medicine-list')

@csrf_exempt
@login_required(login_url='admin_login')
def add_lab_worker(request):
    if request.user.is_hospital_admin:
        admin = Admin_Information.objects.get(user=request.user)
        form = LabWorkerAdminCreationForm(request.POST or None, request.FILES or None)
     
        if request.method == 'POST' and form.is_valid():
            username = (form.cleaned_data.get('username') or '').strip() or generate_unique_user_id('LAB')
            email_addr = form.cleaned_data['email'].strip()
            password = form.cleaned_data.get('password1') or generate_secure_password()

            if User.objects.filter(username=username).exists():
                messages.error(request, 'User ID already exists.')
                return render(request, 'hospital_admin/add-lab-worker.html', {'form': form, 'admin': admin})
            if User.objects.filter(email=email_addr).exists():
                messages.error(request, 'Email already exists.')
                return render(request, 'hospital_admin/add-lab-worker.html', {'form': form, 'admin': admin})

            try:
                with transaction.atomic():
                    lab_user = User.objects.create_user(username=username, email=email_addr, password=password, is_labworker=True)
                    lab_worker, _created = Clinical_Laboratory_Technician.objects.get_or_create(user=lab_user, defaults={'username': username, 'email': email_addr})
                    lab_worker.username = username
                    lab_worker.name = form.cleaned_data['name']
                    lab_worker.email = email_addr
                    lab_worker.age = form.cleaned_data.get('age') or None
                    lab_worker.phone_number = form.cleaned_data.get('phone_number') or None
                    lab_worker.hospital = form.cleaned_data.get('hospital') or None
                    if form.cleaned_data.get('featured_image'):
                        lab_worker.featured_image = form.cleaned_data['featured_image']
                    lab_worker.save()
            except Exception:
                messages.error(request, 'Could not create lab technologist account. Please try again.')
                return render(request, 'hospital_admin/add-lab-worker.html', {'form': form, 'admin': admin})

            sent, reason = send_account_credentials_email(
                role_label='Lab Technologist',
                recipient_name=lab_worker.name or username,
                recipient_email=email_addr,
                user_id=username,
                password=password,
                extra_context={'hospital': str(lab_worker.hospital) if lab_worker.hospital else ''},
            )
            if not sent:
                if reason == 'bad-header':
                    messages.warning(request, 'Lab technologist account created, but email could not be sent (bad header).')
                else:
                    messages.warning(request, 'Lab technologist account created, but email could not be sent.')

            messages.success(request, 'Clinical Laboratory Technician account was created!')
            return redirect('lab-worker-list')
        elif request.method == 'POST':
            messages.error(request, 'An error has occurred during registration')
    
    context = {'form': form, 'admin': admin}
    return render(request, 'hospital_admin/add-lab-worker.html', context)  

@csrf_exempt
@login_required(login_url='admin_login')
def view_lab_worker(request):
    if request.user.is_hospital_admin:
        user = Admin_Information.objects.get(user=request.user)
        search_query = (request.GET.get('q') or '').strip()
        lab_workers = Clinical_Laboratory_Technician.objects.select_related('hospital').all().order_by('-technician_id')
        if search_query:
            lab_workers = lab_workers.filter(
                Q(name__icontains=search_query)
                | Q(username__icontains=search_query)
                | Q(email__icontains=search_query)
                | Q(phone_number__icontains=search_query)
            )
        paginator = Paginator(lab_workers, 10)
        page_obj = paginator.get_page(request.GET.get('page'))
        
    return render(request, 'hospital_admin/lab-worker-list.html', {'lab_workers': page_obj.object_list, 'page_obj': page_obj, 'admin': user, 'search_query': search_query})

@csrf_exempt
@login_required(login_url='admin_login')
def view_pharmacist(request):
    if request.user.is_hospital_admin:
        user = Admin_Information.objects.get(user=request.user)
        pharmcists = Pharmacist.objects.all()
        
    return render(request, 'hospital_admin/pharmacist-list.html', {'pharmacist': pharmcists, 'admin': user})

@csrf_exempt
@login_required(login_url='admin_login')
def edit_lab_worker(request, pk):
    if request.user.is_hospital_admin:
        user = Admin_Information.objects.get(user=request.user)
        lab_worker = Clinical_Laboratory_Technician.objects.get(technician_id=pk)
        form = LabWorkerAdminUpdateForm(request.POST or None, request.FILES or None, instance=lab_worker)

        if request.method == 'POST' and form.is_valid():
            lab_worker = form.save()
            if lab_worker.user:
                lab_worker.user.email = lab_worker.email or lab_worker.user.email
                lab_worker.user.save(update_fields=['email'])
            messages.success(request, 'Clinical Laboratory Technician account updated!')
            return redirect('lab-worker-list')
        
    return render(request, 'hospital_admin/edit-lab-worker.html', {'lab_worker': lab_worker, 'admin': user, 'form': form})

@csrf_exempt
@login_required(login_url='admin_login')
def delete_lab_worker(request, pk):
    if request.method != 'POST' or not request.user.is_hospital_admin:
        return redirect('lab-worker-list')

    lab_worker = get_object_or_404(Clinical_Laboratory_Technician, technician_id=pk)
    if lab_worker.user:
        lab_worker.user.delete()
    else:
        lab_worker.delete()
    messages.success(request, 'Clinical Laboratory Technician account deleted.')
    return redirect('lab-worker-list')

@csrf_exempt
@login_required(login_url='admin_login')
def add_patient(request):
    if not request.user.is_hospital_admin:
        return redirect('admin-logout')

    admin = Admin_Information.objects.get(user=request.user)
    form = PatientAdminCreationForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        username = (form.cleaned_data.get('username') or '').strip() or generate_unique_user_id('PAT')
        email_addr = form.cleaned_data['email'].strip()
        password = form.cleaned_data.get('password1') or generate_secure_password()

        if User.objects.filter(username=username).exists():
            messages.error(request, 'User ID already exists.')
            return render(request, 'hospital_admin/add-patient.html', {'form': form, 'admin': admin})
        if User.objects.filter(email=email_addr).exists():
            messages.error(request, 'Email already exists.')
            return render(request, 'hospital_admin/add-patient.html', {'form': form, 'admin': admin})

        try:
            with transaction.atomic():
                patient_user = User.objects.create_user(username=username, email=email_addr, password=password, is_patient=True)
                patient, _created = Patient.objects.get_or_create(user=patient_user, defaults={'username': username, 'email': email_addr})
                patient.username = username
                patient.name = form.cleaned_data['name']
                patient.email = email_addr
                patient.age = form.cleaned_data.get('age') or None
                patient.phone_number = form.cleaned_data.get('phone_number') or None
                patient.address = form.cleaned_data.get('address') or ''
                patient.blood_group = form.cleaned_data.get('blood_group') or ''
                patient.history = form.cleaned_data.get('history') or ''
                patient.dob = form.cleaned_data.get('dob') or ''
                patient.nid = form.cleaned_data.get('nid') or ''
                if form.cleaned_data.get('featured_image'):
                    patient.featured_image = form.cleaned_data['featured_image']
                patient.save()
        except Exception:
            messages.error(request, 'Could not create patient account. Please try again.')
            return render(request, 'hospital_admin/add-patient.html', {'form': form, 'admin': admin})

        sent, reason = send_account_credentials_email(
            role_label='Patient',
            recipient_name=patient.name or username,
            recipient_email=email_addr,
            user_id=username,
            password=password,
        )
        if not sent:
            if reason == 'bad-header':
                messages.warning(request, 'Patient account created, but email could not be sent (bad header).')
            else:
                messages.warning(request, 'Patient account created, but email could not be sent.')

        messages.success(request, 'Patient account created successfully.')
        return redirect('patient-list')

    return render(request, 'hospital_admin/add-patient.html', {'form': form, 'admin': admin})

@csrf_exempt
@login_required(login_url='admin_login')
def edit_patient(request, pk):
    if not request.user.is_hospital_admin:
        return redirect('admin-logout')

    admin = Admin_Information.objects.get(user=request.user)
    patient = get_object_or_404(Patient, patient_id=pk)
    form = PatientAdminUpdateForm(request.POST or None, request.FILES or None, instance=patient)
    if request.method == 'POST' and form.is_valid():
        patient = form.save()
        if patient.user:
            patient.user.email = patient.email or patient.user.email
            patient.user.save(update_fields=['email'])
        messages.success(request, 'Patient updated successfully.')
        return redirect('patient-list')

    return render(request, 'hospital_admin/edit-patient.html', {'form': form, 'admin': admin, 'patient': patient})

@csrf_exempt
@login_required(login_url='admin_login')
def delete_patient(request, pk):
    if request.method != 'POST' or not request.user.is_hospital_admin:
        return redirect('patient-list')

    patient = get_object_or_404(Patient, patient_id=pk)
    if patient.user:
        patient.user.delete()
    else:
        patient.delete()
    messages.success(request, 'Patient account deleted.')
    return redirect('patient-list')

@csrf_exempt
@login_required(login_url='admin_login')
def edit_pharmacist(request, pk):
    if request.user.is_hospital_admin:
        user = Admin_Information.objects.get(user=request.user)
        pharmacist = Pharmacist.objects.get(pharmacist_id=pk)
        
        if request.method == 'POST':
            if 'featured_image' in request.FILES:
                featured_image = request.FILES['featured_image']
            else:
                featured_image = "technician/user-default.png"
                
            name = request.POST.get('name')
            email = request.POST.get('email')     
            phone_number = request.POST.get('phone_number')
            age = request.POST.get('age')  
    
            pharmacist.name = name
            pharmacist.email = email
            pharmacist.phone_number = phone_number
            pharmacist.age = age
            pharmacist.featured_image = featured_image
    
            pharmacist.save()
            messages.success(request, 'Pharmacist updated!')
            return redirect('pharmacist-list')
        
    return render(request, 'hospital_admin/edit-pharmacist.html', {'pharmacist': pharmacist, 'admin': user})

@csrf_exempt
@login_required(login_url='admin_login')
def department_image_list(request,pk):
    departments = hospital_department.objects.filter(hospital_id=pk)
    #departments = hospital_department.objects.all()
    context = {'departments': departments}
    return render(request, 'hospital_admin/department-image-list.html',context)

@csrf_exempt
@login_required(login_url='admin_login')
def register_doctor_list(request):
    if request.user.is_hospital_admin:
        user = Admin_Information.objects.get(user=request.user)
        # Data safety: ensure every doctor user has a Doctor_Information profile.
        # This prevents situations where a doctor account exists but doesn't show in the registered list.
        for doctor_user in User.objects.filter(is_doctor=True):
            profile, _created = Doctor_Information.objects.get_or_create(
                user=doctor_user,
                defaults={
                    'username': doctor_user.username,
                    'email': doctor_user.email,
                    'register_status': 'Accepted',
                },
            )
            if not profile.register_status:
                profile.register_status = 'Accepted'
                profile.save(update_fields=['register_status'])

        search_query = (request.GET.get('q') or '').strip()
        doctors = Doctor_Information.objects.filter(register_status='Accepted').select_related('hospital_name', 'specialization').order_by('-doctor_id')
        if search_query:
            doctors = doctors.filter(
                Q(name__icontains=search_query)
                | Q(username__icontains=search_query)
                | Q(email__icontains=search_query)
                | Q(hospital_name__name__icontains=search_query)
            )
        paginator = Paginator(doctors, 10)
        page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'hospital_admin/register-doctor-list.html', {'doctors': page_obj.object_list, 'page_obj': page_obj, 'admin': user, 'search_query': search_query})

@csrf_exempt
@login_required(login_url='admin_login')
def pending_doctor_list(request):
    # Doctor self-registration is disabled and admin-created doctors are auto-accepted.
    # Keep this route for backwards compatibility, but route admins to Registered.
    messages.info(request, 'Pending doctors section is disabled. Showing registered doctors instead.')
    return redirect('register-doctor-list')


@csrf_exempt
@login_required(login_url='admin_login')
def add_doctor(request):
    if not request.user.is_hospital_admin:
        return redirect('admin-logout')

    admin = Admin_Information.objects.get(user=request.user)
    form = DoctorAccountCreationForm(request.POST or None, request.FILES or None)

    if request.method == 'POST' and form.is_valid():
        username = (form.cleaned_data.get('username') or '').strip()
        email_addr = form.cleaned_data['email'].strip()
        password = form.cleaned_data.get('password1')
        if not password:
            password = generate_secure_password()
        if not username:
            username = generate_unique_user_id('DOC')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'User ID already exists.')
            return render(request, 'hospital_admin/add-doctor.html', {'form': form, 'admin': admin})
        if User.objects.filter(email=email_addr).exists():
            messages.error(request, 'Email already exists.')
            return render(request, 'hospital_admin/add-doctor.html', {'form': form, 'admin': admin})

        try:
            with transaction.atomic():
                # Create doctor user with is_doctor=True so the signal creates a profile reliably.
                user = User.objects.create_user(
                    username=username,
                    email=email_addr,
                    password=password,
                    is_doctor=True,
                )

                # Signal should have created it; keep a safe fallback.
                doctor, _created = Doctor_Information.objects.get_or_create(
                    user=user,
                    defaults={
                        'username': username,
                        'email': email_addr,
                    },
                )

                doctor.username = username
                doctor.name = form.cleaned_data['name']
                doctor.gender = form.cleaned_data.get('gender') or ''
                doctor.description = form.cleaned_data.get('description') or ''
                doctor.department = form.cleaned_data.get('department') or None
                doctor.department_name = form.cleaned_data.get('department_name') or None
                doctor.specialization = form.cleaned_data.get('specialization') or None
                doctor.hospital_name = form.cleaned_data['hospital_name']
                doctor.email = form.cleaned_data.get('email_profile') or email_addr
                doctor.phone_number = form.cleaned_data.get('phone_number') or ''
                doctor.nid = form.cleaned_data.get('nid') or ''
                doctor.dob = form.cleaned_data.get('dob') or ''
                doctor.visiting_hour = form.cleaned_data.get('visiting_hour') or ''
                doctor.consultation_fee = form.cleaned_data.get('consultation_fee') or None
                doctor.report_fee = form.cleaned_data.get('report_fee') or None
                doctor.institute = form.cleaned_data.get('institute') or ''
                doctor.degree = form.cleaned_data.get('degree') or ''
                doctor.completion_year = form.cleaned_data.get('completion_year') or ''
                doctor.work_place = form.cleaned_data.get('work_place') or ''
                doctor.designation = form.cleaned_data.get('designation') or ''
                doctor.start_year = form.cleaned_data.get('start_year') or ''
                doctor.end_year = form.cleaned_data.get('end_year') or ''
                doctor.register_status = 'Accepted'

                if form.cleaned_data.get('featured_image'):
                    doctor.featured_image = form.cleaned_data['featured_image']
                if form.cleaned_data.get('certificate_image'):
                    doctor.certificate_image = form.cleaned_data['certificate_image']

                doctor.save()

                additional_hospitals = form.cleaned_data.get('additional_hospitals')
                if additional_hospitals is not None:
                    doctor.appointed_hospitals.set(additional_hospitals)
        except Exception:
            messages.error(request, 'Could not create doctor account. Please try again.')
            return render(request, 'hospital_admin/add-doctor.html', {'form': form, 'admin': admin})

        sent, reason = send_account_credentials_email(
            role_label='Doctor',
            recipient_name=doctor.name or username,
            recipient_email=email_addr,
            user_id=username,
            password=password,
            extra_context={'hospital': str(doctor.hospital_name) if doctor.hospital_name else ''},
        )
        if not sent:
            if reason == 'bad-header':
                messages.warning(request, 'Doctor account created, but email could not be sent (bad header).')
            else:
                messages.warning(request, 'Doctor account created, but email could not be sent.')

        messages.success(request, 'Doctor account created successfully.')
        return redirect('register-doctor-list')

    return render(request, 'hospital_admin/add-doctor.html', {'form': form, 'admin': admin})


@csrf_exempt
@login_required(login_url='admin_login')
def edit_doctor(request, pk):
    if not request.user.is_hospital_admin:
        return redirect('admin-logout')

    admin = Admin_Information.objects.get(user=request.user)
    doctor = get_object_or_404(Doctor_Information, doctor_id=pk)

    initial = {
        'name': doctor.name,
        'gender': doctor.gender,
        'description': doctor.description,
        'hospital_name': doctor.hospital_name,
        'additional_hospitals': doctor.appointed_hospitals.all(),
        'department': doctor.department,
        'department_name': doctor.department_name,
        'specialization': doctor.specialization,
        'email': doctor.email,
        'phone_number': doctor.phone_number,
        'nid': doctor.nid,
        'dob': doctor.dob,
        'visiting_hour': doctor.visiting_hour,
        'consultation_fee': doctor.consultation_fee,
        'report_fee': doctor.report_fee,
        'institute': doctor.institute,
        'degree': doctor.degree,
        'completion_year': doctor.completion_year,
        'work_place': doctor.work_place,
        'designation': doctor.designation,
        'start_year': doctor.start_year,
        'end_year': doctor.end_year,
    }
    form = DoctorAdminUpdateForm(request.POST or None, request.FILES or None, initial=initial)

    if request.method == 'POST' and form.is_valid():
        doctor.name = form.cleaned_data['name']
        doctor.gender = form.cleaned_data.get('gender') or ''
        doctor.description = form.cleaned_data.get('description') or ''
        doctor.hospital_name = form.cleaned_data['hospital_name']
        additional_hospitals = form.cleaned_data.get('additional_hospitals')
        if additional_hospitals is not None:
            doctor.appointed_hospitals.set(additional_hospitals)
        doctor.department = form.cleaned_data.get('department') or None
        doctor.department_name = form.cleaned_data.get('department_name') or None
        doctor.specialization = form.cleaned_data.get('specialization') or None
        doctor.email = form.cleaned_data.get('email') or doctor.email
        doctor.phone_number = form.cleaned_data.get('phone_number') or ''
        doctor.nid = form.cleaned_data.get('nid') or ''
        doctor.dob = form.cleaned_data.get('dob') or ''
        doctor.visiting_hour = form.cleaned_data.get('visiting_hour') or ''
        doctor.consultation_fee = form.cleaned_data.get('consultation_fee') or None
        doctor.report_fee = form.cleaned_data.get('report_fee') or None
        doctor.institute = form.cleaned_data.get('institute') or ''
        doctor.degree = form.cleaned_data.get('degree') or ''
        doctor.completion_year = form.cleaned_data.get('completion_year') or ''
        doctor.work_place = form.cleaned_data.get('work_place') or ''
        doctor.designation = form.cleaned_data.get('designation') or ''
        doctor.start_year = form.cleaned_data.get('start_year') or ''
        doctor.end_year = form.cleaned_data.get('end_year') or ''
        if form.cleaned_data.get('featured_image'):
            doctor.featured_image = form.cleaned_data['featured_image']
        if form.cleaned_data.get('certificate_image'):
            doctor.certificate_image = form.cleaned_data['certificate_image']
        doctor.save()
        if doctor.user:
            doctor.user.email = doctor.email or doctor.user.email
            doctor.user.save(update_fields=['email'])

        messages.success(request, 'Doctor updated successfully.')
        return redirect('admin-doctor-profile', pk=doctor.doctor_id)

    return render(request, 'hospital_admin/edit-doctor.html', {'form': form, 'admin': admin, 'doctor': doctor})

@csrf_exempt
@login_required(login_url='admin_login')
def delete_doctor(request, pk):
    if request.method != 'POST' or not request.user.is_hospital_admin:
        return redirect('register-doctor-list')

    doctor = get_object_or_404(Doctor_Information, doctor_id=pk)
    if doctor.user:
        doctor.user.delete()
    else:
        doctor.delete()
    messages.success(request, 'Doctor account deleted.')
    return redirect('register-doctor-list')

@csrf_exempt
@login_required(login_url='admin_login')
def update_appointment_status(request, pk):
    if request.method != 'POST' or not request.user.is_hospital_admin:
        return redirect('appointment-list')

    appointment = get_object_or_404(Appointment, id=pk)
    new_status = (request.POST.get('appointment_status') or '').strip()
    allowed_statuses = {choice[0] for choice in Appointment.APPOINTMENT_STATUS}
    if new_status not in allowed_statuses:
        messages.error(request, 'Invalid appointment status.')
        return redirect('appointment-list')

    appointment.appointment_status = new_status
    appointment.save(update_fields=['appointment_status'])
    messages.success(request, 'Appointment status updated successfully.')
    return redirect('appointment-list')

@csrf_exempt
@login_required(login_url='admin_login')
def admin_doctor_profile(request,pk):
    doctor = Doctor_Information.objects.get(doctor_id=pk)
    admin = Admin_Information.objects.get(user=request.user)
    experience= Experience.objects.filter(doctor_id=pk).order_by('-from_year','-to_year')
    education = Education.objects.filter(doctor_id=pk).order_by('-year_of_completion')
    
    context = {'doctor': doctor, 'admin': admin, 'experiences': experience, 'educations': education}
    return render(request, 'hospital_admin/doctor-profile.html',context)


@csrf_exempt
@login_required(login_url='admin_login')
def accept_doctor(request,pk):
    doctor = Doctor_Information.objects.get(doctor_id=pk)
    doctor.register_status = 'Accepted'
    doctor.save()
    
    experience= Experience.objects.filter(doctor_id=pk)
    education = Education.objects.filter(doctor_id=pk)
    
    # Mailtrap
    doctor_name = doctor.name
    doctor_email = doctor.email
    doctor_department = doctor.department_name.hospital_department_name

    doctor_specialization = doctor.specialization.specialization_name

    subject = "Acceptance of Doctor Registration"

    values = {
            "doctor_name":doctor_name,
            "doctor_email":doctor_email,
            "doctor_department":doctor_department,

            "doctor_specialization":doctor_specialization,
        }

    html_message = render_to_string('hospital_admin/accept-doctor-mail.html', {'values': values})
    plain_message = strip_tags(html_message)

    try:
        send_mail(subject, plain_message, 'hospital_admin@gmail.com',  [doctor_email], html_message=html_message, fail_silently=False)
    except BadHeaderError:
        return HttpResponse('Invalid header found')

    messages.success(request, 'Doctor Accepted!')
    return redirect('register-doctor-list')


@csrf_exempt
@login_required(login_url='admin_login')
def reject_doctor(request,pk):
    doctor = Doctor_Information.objects.get(doctor_id=pk)
    doctor.register_status = 'Rejected'
    doctor.save()
    
    # Mailtrap
    doctor_name = doctor.name
    doctor_email = doctor.email
    doctor_department = doctor.department_name.hospital_department_name
    doctor_hospital = doctor.hospital_name.name
    doctor_specialization = doctor.specialization.specialization_name

    subject = "Rejection of Doctor Registration"

    values = {
            "doctor_name":doctor_name,
            "doctor_email":doctor_email,
            "doctor_department":doctor_department,
            "doctor_hospital":doctor_hospital,
            "doctor_specialization":doctor_specialization,
        }

    html_message = render_to_string('hospital_admin/reject-doctor-mail.html', {'values': values})
    plain_message = strip_tags(html_message)

    try:
        send_mail(subject, plain_message, 'hospital_admin@gmail.com',  [doctor_email], html_message=html_message, fail_silently=False)
    except BadHeaderError:
        return HttpResponse('Invalid header found')
    
    messages.success(request, 'Doctor Rejected!')
    return redirect('register-doctor-list')

@csrf_exempt
@login_required(login_url='admin_login')
def delete_department(request,pk):
    if request.user.is_authenticated:
        if request.user.is_hospital_admin:
            department = hospital_department.objects.get(hospital_department_id=pk)
            department.delete()
            messages.success(request, 'Department Deleted!')
            return redirect('hospital-list')

@login_required(login_url='admin_login')
@csrf_exempt
def edit_department(request,pk):
    if request.user.is_authenticated:
        if request.user.is_hospital_admin:
            # old_featured_image = department.featured_image
            department = hospital_department.objects.get(hospital_department_id=pk)
            old_featured_image = department.featured_image

            if request.method == 'POST':
                if 'featured_image' in request.FILES:
                    featured_image = request.FILES['featured_image']
                else:
                    featured_image = old_featured_image

                department_name = request.POST.get('department_name')
                department.hospital_department_name = department_name
                department.featured_image = featured_image
                department.save()
                messages.success(request, 'Department Updated!')
                return redirect('hospital-list')
                
            context = {'department': department}
            return render(request, 'hospital_admin/edit-hospital.html',context)

@csrf_exempt
@login_required(login_url='admin_login')
def labworker_dashboard(request):
    if request.user.is_authenticated:
        if request.user.is_labworker:
            
            lab_workers = Clinical_Laboratory_Technician.objects.get(user=request.user)
            doctor = Doctor_Information.objects.all()
            context = {'doctor': doctor,'lab_workers':lab_workers}
            return render(request, 'hospital_admin/labworker-dashboard.html',context)

@csrf_exempt
@login_required(login_url='admin-login')
def mypatient_list(request):
    if request.user.is_authenticated:
        if request.user.is_labworker:
            lab_workers = Clinical_Laboratory_Technician.objects.get(user=request.user)
            #report= Report.objects.all()
            patient = Patient.objects.all()
            context = {'patient': patient,'lab_workers':lab_workers}
            return render(request, 'hospital_admin/mypatient-list.html',context)

@csrf_exempt
@login_required(login_url='admin-login')
def prescription_list(request,pk):
    if request.user.is_authenticated:
        if request.user.is_labworker:
            lab_workers = Clinical_Laboratory_Technician.objects.get(user=request.user)
            patient = Patient.objects.get(patient_id=pk)
            prescription = Prescription.objects.filter(patient=patient)
            context = {'prescription': prescription,'lab_workers':lab_workers,'patient':patient}
            return render(request, 'hospital_admin/prescription-list.html',context)

@csrf_exempt
@login_required(login_url='admin-login')
def add_test(request):
    if request.user.is_labworker:
        lab_workers = Clinical_Laboratory_Technician.objects.get(user=request.user)

    if request.method == 'POST':
        tests=Test_Information()
        test_name = request.POST['test_name']
        test_price = request.POST['test_price']
        tests.test_name = test_name
        tests.test_price = test_price

        tests.save()

        return redirect('test-list')
        
    context = {'lab_workers': lab_workers}
    return render(request, 'hospital_admin/add-test.html', context)

@csrf_exempt
@login_required(login_url='admin-login')
def test_list(request):
    if request.user.is_labworker:
        lab_workers = Clinical_Laboratory_Technician.objects.get(user=request.user)
        test = Test_Information.objects.all()
        context = {'test':test,'lab_workers':lab_workers}
    return render(request, 'hospital_admin/test-list.html',context)


@csrf_exempt
@login_required(login_url='admin-login')
def delete_test(request,pk):
    if request.user.is_authenticated:
        if request.user.is_labworker:
            test = Test_Information.objects.get(test_id=pk)
            test.delete()
            return redirect('test-list')

@csrf_exempt
def pharmacist_dashboard(request):
    if request.user.is_authenticated:
        if request.user.is_pharmacist:
            pharmacist = Pharmacist.objects.get(user=request.user)
            total_pharmacist_count = Pharmacist.objects.annotate(count=Count('pharmacist_id'))
            total_medicine_count = Medicine.objects.annotate(count=Count('serial_number'))
            total_order_count = Order.objects.annotate(count=Count('orderitems'))
            total_cart_count = Cart.objects.annotate(count=Count('item'))

            medicine = Medicine.objects.all()
            
            context = {'pharmacist':pharmacist, 'medicine':medicine,
                       'total_pharmacist_count':total_pharmacist_count, 
                       'total_medicine_count':total_medicine_count, 
                       'total_order_count':total_order_count,
                       'total_cart_count':total_cart_count}
            return render(request, 'hospital_admin/pharmacist-dashboard.html',context)

@csrf_exempt
def report_history(request):
    if request.user.is_authenticated:
        if request.user.is_labworker:

            lab_workers = Clinical_Laboratory_Technician.objects.get(user=request.user)
            report = Report.objects.all()
            context = {'report':report,'lab_workers':lab_workers}
            return render(request, 'hospital_admin/report-list.html',context)


# ── Finance Module ────────────────────────────────────────────────────────────

def _finance_safe_amount(p):
    """Return float value of a Payment.currency_amount safely."""
    try:
        return float(p.currency_amount or 0)
    except (ValueError, TypeError):
        return 0.0


def _month_label(m):
    """Convert 'YYYY-MM' string to 'Mon YYYY' label."""
    from calendar import month_abbr
    try:
        y, mo = m.split('-')
        return month_abbr[int(mo)] + ' ' + y
    except Exception:
        return m


@login_required(login_url='admin_login')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def payment_overview(request):
    if not request.user.is_hospital_admin:
        return redirect('admin-logout')
    admin = Admin_Information.objects.get(user=request.user)

    today      = datetime.date.today()
    month_str  = today.strftime('%Y-%m')
    week_start = today - datetime.timedelta(days=today.weekday())

    all_payments   = list(Payment.objects.select_related(
        'patient', 'appointment', 'appointment__doctor'
    ).all())
    valid_payments = [p for p in all_payments if p.status == 'VALID']

    def _date_starts(p, prefix):
        return p.transaction_date and str(p.transaction_date).startswith(str(prefix))

    total_revenue   = sum(_finance_safe_amount(p) for p in valid_payments)
    today_revenue   = sum(_finance_safe_amount(p) for p in valid_payments if _date_starts(p, today))
    monthly_revenue = sum(_finance_safe_amount(p) for p in valid_payments if _date_starts(p, month_str))

    weekly_revenue = 0.0
    for p in valid_payments:
        if p.transaction_date:
            try:
                d = datetime.datetime.strptime(str(p.transaction_date)[:10], '%Y-%m-%d').date()
                if week_start <= d <= today:
                    weekly_revenue += _finance_safe_amount(p)
            except (ValueError, TypeError):
                pass

    # Monthly revenue chart (last 6 months)
    monthly_data = {}
    for p in valid_payments:
        if p.transaction_date:
            m = str(p.transaction_date)[:7]
            if len(m) == 7 and '-' in m:
                monthly_data[m] = monthly_data.get(m, 0) + _finance_safe_amount(p)
    sorted_months = sorted(monthly_data.keys())[-6:]
    revenue_chart_labels = [_month_label(m) for m in sorted_months]
    revenue_chart_data   = [round(monthly_data.get(m, 0), 2) for m in sorted_months]

    # Payment type distribution (doughnut)
    ptype_data = {}
    for p in valid_payments:
        ptype = (p.payment_type or 'Other').replace('_', ' ').title()
        ptype_data[ptype] = ptype_data.get(ptype, 0) + _finance_safe_amount(p)

    # Recent 8 valid transactions
    recent_transactions = sorted(valid_payments, key=lambda p: p.payment_id, reverse=True)[:8]

    # Appointment payment stats
    total_appointments  = Appointment.objects.count()
    paid_appointments   = Appointment.objects.filter(payment_status='Paid').count()

    context = {
        'admin': admin,
        'total_revenue':     round(total_revenue, 2),
        'today_revenue':     round(today_revenue, 2),
        'monthly_revenue':   round(monthly_revenue, 2),
        'weekly_revenue':    round(weekly_revenue, 2),
        'total_transactions': len(all_payments),
        'paid_count':        sum(1 for p in all_payments if p.status == 'VALID'),
        'pending_count':     sum(1 for p in all_payments if p.status not in ('VALID', 'VALIDATED', None, '')),
        'recent_transactions': recent_transactions,
        'revenue_chart_labels': revenue_chart_labels,
        'revenue_chart_data':   revenue_chart_data,
        'ptype_labels':  list(ptype_data.keys()),
        'ptype_data':    [round(v, 2) for v in ptype_data.values()],
        'total_appointments':  total_appointments,
        'paid_appointments':   paid_appointments,
        'unpaid_appointments': total_appointments - paid_appointments,
    }
    return render(request, 'hospital_admin/finance-overview.html', context)


@login_required(login_url='admin_login')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def revenue_reports(request):
    if not request.user.is_hospital_admin:
        return redirect('admin-logout')
    admin = Admin_Information.objects.get(user=request.user)

    today     = datetime.date.today()
    month_str = today.strftime('%Y-%m')

    all_payments   = list(Payment.objects.select_related(
        'patient', 'appointment', 'appointment__doctor'
    ).all())
    valid_payments = [p for p in all_payments if p.status == 'VALID']

    # Monthly aggregation
    monthly_data   = {}
    monthly_counts = {}
    for p in valid_payments:
        if p.transaction_date:
            m = str(p.transaction_date)[:7]
            if len(m) == 7 and '-' in m:
                monthly_data[m]   = monthly_data.get(m, 0)   + _finance_safe_amount(p)
                monthly_counts[m] = monthly_counts.get(m, 0) + 1

    sorted_months    = sorted(monthly_data.keys())
    monthly_summary  = [
        {
            'month':   _month_label(m),
            'revenue': round(monthly_data[m], 2),
            'count':   monthly_counts.get(m, 0),
        }
        for m in sorted_months
    ]

    # Bar chart: last 12 months
    chart_months = sorted_months[-12:]
    bar_labels   = [_month_label(m) for m in chart_months]
    bar_data     = [round(monthly_data.get(m, 0), 2) for m in chart_months]

    # Daily earnings for current month (line chart)
    daily_data = {}
    for p in valid_payments:
        if p.transaction_date and str(p.transaction_date).startswith(month_str):
            d = str(p.transaction_date)[:10]
            daily_data[d] = daily_data.get(d, 0) + _finance_safe_amount(p)
    sorted_days  = sorted(daily_data.keys())
    daily_labels = [d[8:] for d in sorted_days]   # day number within month
    daily_values = [round(daily_data[d], 2) for d in sorted_days]

    # Doctor-wise revenue (top 8)
    doctor_revenue = {}
    for p in valid_payments:
        if p.appointment and p.appointment.doctor:
            doc_name = p.appointment.doctor.name or 'Unknown'
            doctor_revenue[doc_name] = doctor_revenue.get(doc_name, 0) + _finance_safe_amount(p)
    top_doctors = sorted(doctor_revenue.items(), key=lambda x: x[1], reverse=True)[:8]

    context = {
        'admin':            admin,
        'monthly_summary':  monthly_summary,
        'bar_labels':       bar_labels,
        'bar_data':         bar_data,
        'daily_labels':     daily_labels,
        'daily_values':     daily_values,
        'top_doctor_labels': [d[0] for d in top_doctors],
        'top_doctor_data':   [round(d[1], 2) for d in top_doctors],
        'total_revenue':     round(sum(_finance_safe_amount(p) for p in valid_payments), 2),
        'current_month':     today.strftime('%B %Y'),
    }
    return render(request, 'hospital_admin/revenue-reports.html', context)


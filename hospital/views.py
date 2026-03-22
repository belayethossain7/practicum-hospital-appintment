import email
from multiprocessing import context
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
# from django.contrib.auth.models import User
# from django.contrib.auth.forms import UserCreationForm
from .forms import CustomUserCreationForm, PatientForm, PasswordResetForm
from hospital.models import Hospital_Information, User, Patient 
from doctor.models import Test, testCart, testOrder
from hospital_admin.models import hospital_department, specialization, service, Test_Information
from django.views.decorators.cache import cache_control
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from datetime import datetime
import datetime
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.template.loader import get_template
from xhtml2pdf import pisa
from .utils import searchDoctors, searchHospitals, searchDepartmentDoctors, paginateHospitals, paginateDoctors
from .models import Patient, User
from doctor.models import Doctor_Information, Appointment,Report, Specimen, Test, Prescription, Prescription_medicine, Prescription_test
from sslcommerz.models import Payment
from django.db.models import Q, Count
import re
from io import BytesIO
from urllib import response
from django.core.mail import BadHeaderError, send_mail
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.utils.http import url_has_allowed_host_and_scheme
from datetime import timedelta

from doctor.slots import get_available_slot_labels, parse_appointment_date
from doctor.models import Doctor_review


# Create your views here.
@csrf_exempt
def hospital_home(request):
    context = _build_hospital_home_context(request)
    return render(request, 'index-2.html', context)


def _build_hospital_home_context(request):
    today = timezone.localdate()
    now_local = timezone.localtime(timezone.now())

    hospital_id = (request.GET.get('hospital') or '').strip()
    specialization_id = (request.GET.get('specialization') or '').strip()
    doctor_id = (request.GET.get('doctor') or '').strip()
    date_str = (request.GET.get('date') or '').strip()
    time_str = (request.GET.get('time') or '').strip()
    query = (request.GET.get('q') or '').strip()

    doctors_qs = (
        Doctor_Information.objects.filter(register_status='Accepted', hospital_name__isnull=False)
        .select_related('hospital_name', 'specialization', 'department_name')
    )

    if hospital_id.isdigit():
        doctors_qs = doctors_qs.filter(hospital_name_id=int(hospital_id))

    if specialization_id.isdigit():
        doctors_qs = doctors_qs.filter(specialization_id=int(specialization_id))

    if query:
        doctors_qs = doctors_qs.filter(
            Q(name__icontains=query)
            | Q(hospital_name__name__icontains=query)
            | Q(department_name__hospital_department_name__icontains=query)
            | Q(specialization__specialization_name__icontains=query)
        )

    selected_date = None
    if date_str:
        try:
            selected_date = parse_appointment_date(date_str)
        except ValueError:
            selected_date = None

    if selected_date:
        date_range = [selected_date]
    else:
        date_range = [today + timedelta(days=i) for i in range(0, 7)]

    slot_cards_source_qs = (
        Doctor_Information.objects.filter(register_status='Accepted', hospital_name__isnull=False)
        .select_related('hospital_name', 'specialization', 'department_name')
    )
    slot_cards = _build_slot_cards(slot_cards_source_qs, date_range, now_local=now_local, limit=200)

    hospitals_all = Hospital_Information.objects.all().order_by('name', 'address')

    # NOTE: Booking filters (hospital/specialization/doctor/date/time) should not change
    # other home sections (Hospitals slider, Quick Booking cards, etc.).
    selected_hospital = None
    hospital_branches = []

    featured_hospital_ids = (
        Doctor_Information.objects.filter(register_status='Accepted', hospital_name__isnull=False)
        .values('hospital_name_id')
        .annotate(total=Count('doctor_id'))
        .order_by('-total')
        .values_list('hospital_name_id', flat=True)[:6]
    )
    featured_hospitals = list(Hospital_Information.objects.filter(hospital_id__in=list(featured_hospital_ids)))

    available_doctors = list(doctors_qs[:8])

    specialization_options = (
        Doctor_Information.objects.filter(register_status='Accepted')
        .exclude(specialization__isnull=True)
        .values('specialization_id', 'specialization__specialization_name')
        .distinct()
        .order_by('specialization__specialization_name')
    )

    testimonials = (
        Doctor_review.objects.select_related('patient', 'doctor')
        .exclude(patient__isnull=True)
        .exclude(doctor__isnull=True)
        .exclude(message__isnull=True)
        .exclude(message='')
        .order_by('-review_id')[:6]
    )

    stats = {
        'hospitals': Hospital_Information.objects.count(),
        'doctors': Doctor_Information.objects.filter(register_status='Accepted').count(),
        'patients': Patient.objects.count(),
    }

    context = {
        'today_iso': today.isoformat(),
        'hospitals': hospitals_all,
        'selected_hospital': selected_hospital,
        'hospital_branches': hospital_branches,
        'featured_hospitals': featured_hospitals,
        'doctors': doctors_qs,
        'available_doctors': available_doctors,
        'carousel_doctors': list(Doctor_Information.objects.filter(register_status='Accepted', hospital_name__isnull=False).select_related('hospital_name')[:24]),
        'slot_cards': slot_cards,
        'specialization_options': specialization_options,
        'testimonials': testimonials,
        'stats': stats,
        'filters': {
            'hospital': hospital_id,
            'specialization': specialization_id,
            'doctor': doctor_id,
            'date': selected_date.isoformat() if selected_date else date_str,
            'time': time_str,
            'q': query,
        },
    }
    return context


@csrf_exempt
def hospital_home_specializations(request):
    """AJAX: specializations for a given hospital based on accepted doctors."""
    hospital_id = (request.GET.get('hospital') or '').strip()
    if not hospital_id.isdigit():
        return JsonResponse({'items': []})

    items = (
        Doctor_Information.objects.filter(register_status='Accepted', hospital_name_id=int(hospital_id))
        .exclude(specialization__isnull=True)
        .values('specialization_id', 'specialization__specialization_name')
        .distinct()
        .order_by('specialization__specialization_name')
    )

    return JsonResponse({'items': list(items)})


@csrf_exempt
def hospital_home_doctors(request):
    """AJAX: doctors for hospital + specialization (optional) + search query."""
    hospital_id = (request.GET.get('hospital') or '').strip()
    specialization_id = (request.GET.get('specialization') or '').strip()
    query = (request.GET.get('q') or '').strip()

    qs = Doctor_Information.objects.filter(register_status='Accepted', hospital_name__isnull=False).select_related(
        'hospital_name', 'specialization', 'department_name'
    )
    if hospital_id.isdigit():
        qs = qs.filter(hospital_name_id=int(hospital_id))
    if specialization_id.isdigit():
        qs = qs.filter(specialization_id=int(specialization_id))
    if query:
        qs = qs.filter(Q(name__icontains=query) | Q(hospital_name__name__icontains=query))

    items = []
    for d in qs.order_by('name')[:200]:
        spec = ''
        if getattr(d, 'specialization', None):
            spec = d.specialization.specialization_name or ''
        elif getattr(d, 'department_name', None):
            spec = d.department_name.hospital_department_name or ''
        items.append({
            'doctor_id': d.doctor_id,
            'name': d.name,
            'specialization': spec,
            'hospital_id': d.hospital_name_id,
            'hospital_name': getattr(d.hospital_name, 'name', '') or '',
        })

    return JsonResponse({'items': items})


@csrf_exempt
def hospital_home_available_slots(request):
    """AJAX: available slots for a doctor on a given date (YYYY-MM-DD)."""
    doctor_id = (request.GET.get('doctor') or '').strip()
    date_str = (request.GET.get('date') or '').strip()
    if not doctor_id.isdigit() or not date_str:
        return JsonResponse({'items': [], 'detail': 'Missing doctor/date'})

    doctor = Doctor_Information.objects.filter(doctor_id=int(doctor_id), register_status='Accepted').first()
    if not doctor:
        return JsonResponse({'items': [], 'detail': 'Doctor not found'}, status=404)

    try:
        date_value = parse_appointment_date(date_str)
    except ValueError:
        return JsonResponse({'items': [], 'detail': 'Invalid date'}, status=400)

    now_local = timezone.localtime(timezone.now())
    available = get_available_slot_labels(doctor, date_value, now_local=now_local)
    return JsonResponse({
        'items': available,
        'is_today': str(date_value) == str(timezone.localdate()),
        'slots_left': len(available),
    })


def hospital_branch_doctors(request, pk):
    """Public page: doctors for a specific hospital branch (Hospital_Information)."""
    hospital = get_object_or_404(Hospital_Information, hospital_id=pk)
    doctors = (
        Doctor_Information.objects.filter(register_status='Accepted', hospital_name=hospital)
        .select_related('specialization', 'department_name', 'hospital_name')
        .order_by('name')
    )
    return render(request, 'hospital-branch-doctors.html', {'hospital': hospital, 'doctors': doctors})


def _build_slot_cards(doctors_qs, date_range, *, now_local, limit: int):
    cards = []
    if not date_range:
        return cards

    today = timezone.localdate()

    # Iterate doctors first so we can show a wider spread of doctors (one upcoming slot each).
    for doctor in doctors_qs.order_by('name'):
        if doctor.hospital_name_id is None:
            continue

        chosen_date = None
        chosen_time = None
        chosen_available_count = 0
        for date_value in date_range:
            available = get_available_slot_labels(doctor, date_value, now_local=now_local)
            if not available:
                continue
            chosen_date = date_value
            chosen_time = available[0]
            chosen_available_count = len(available)
            break

        if not chosen_date or not chosen_time:
            continue

        cards.append({
            'doctor': doctor,
            'hospital': doctor.hospital_name,
            'specialization': getattr(getattr(doctor, 'specialization', None), 'specialization_name', '')
            or getattr(getattr(doctor, 'department_name', None), 'hospital_department_name', '')
            or '',
            'location': getattr(doctor.hospital_name, 'address', '') or '',
            'date': chosen_date,
            'time': chosen_time,
            'is_today': (chosen_date == today),
            'slots_left_today': chosen_available_count,
        })
        if len(cards) >= limit:
            return cards

    return cards


@csrf_exempt
def hospital_home_slots(request):
    """AJAX endpoint: returns just the slot-card HTML based on filters."""
    context = _build_hospital_home_context(request)
    html = render_to_string('partials/appointment_slot_cards.html', {'slot_cards': context.get('slot_cards', [])}, request=request)
    return JsonResponse({
        'html': html,
        'count': len(context.get('slot_cards', [])),
    })

@csrf_exempt
@login_required(login_url="login")
def change_password(request,pk):
    patient = Patient.objects.get(user_id=pk)
    context={"patient":patient}
    if request.method == "POST":
        new_password = request.POST["new_password"]
        confirm_password = request.POST["confirm_password"]
        if new_password == confirm_password:
            
            request.user.set_password(new_password)
            request.user.save()
            messages.success(request,"Password Changed Successfully")
            return redirect("patient-dashboard")
        else:
            messages.error(request,"New Password and Confirm Password is not same")
            return redirect("change-password",pk)
    return render(request, 'change-password.html',context)


def add_billing(request):
    return render(request, 'add-billing.html')

def appointments(request):
    return render(request, 'appointments.html')

def edit_billing(request):
    return render(request, 'edit-billing.html')

def edit_prescription(request):
    return render(request, 'edit-prescription.html')

# def forgot_password(request):
#     return render(request, 'forgot-password.html')

@csrf_exempt
def resetPassword(request):
    form = PasswordResetForm()

    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user_email = user.email
       
            subject = "Password Reset Requested"
            # email_template_name = "password_reset_email.txt"
            values = {
				"email":user.email,
				'domain':'127.0.0.1:8000',
				'site_name': 'Website',
				"uid": urlsafe_base64_encode(force_bytes(user.pk)),
				"user": user,
				'token': default_token_generator.make_token(user),
				'protocol': 'http',
			}

            html_message = render_to_string('mail_template.html', {'values': values})
            plain_message = strip_tags(html_message)
            
            try:
                send_mail(subject, plain_message, 'admin@example.com',  [user.email], html_message=html_message, fail_silently=False)
            except BadHeaderError:
                return HttpResponse('Invalid header found.')
            return redirect ("password_reset_done")

    context = {'form': form}
    return render(request, 'reset_password.html', context)
    
    
def privacy_policy(request):
    return render(request, 'privacy-policy.html')

def about_us(request):
    return render(request, 'about-us.html')

@csrf_exempt
@login_required(login_url="login")
def chat(request, pk):
    patient = Patient.objects.get(user_id=pk)
    doctors = Doctor_Information.objects.filter(register_status='Accepted')

    context = {'patient': patient, 'doctors': doctors}
    return render(request, 'chat.html', context)

@csrf_exempt
@login_required(login_url="login")
def chat_doctor(request):
    if request.user.is_doctor:
        doctor = Doctor_Information.objects.get(user=request.user)
        patients = Patient.objects.all()
        
    context = {'patients': patients, 'doctor': doctor}
    return render(request, 'chat-doctor.html', context)

@csrf_exempt     
@login_required(login_url="login")
def pharmacy_shop(request):
    return render(request, 'pharmacy/shop.html')

@csrf_exempt
def login_user(request):
    page = 'patient_login'
    if request.method == 'GET':
        return render(request, 'patient-login.html')
    elif request.method == 'POST':
        next_url = request.POST.get('next') or request.GET.get('next')
        username = request.POST['username']
        password = request.POST['password']

        try:
            user = User.objects.get(username=username)
        except:
            messages.error(request, 'Username does not exist')

        user = authenticate(username=username, password=password)

        if user is not None:
            login(request, user)
            if request.user.is_patient:   
                messages.success(request, 'User Logged in Successfully')    
                if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
                    return redirect(next_url)
                return redirect('patient-dashboard')
            else:
                messages.error(request, 'Invalid credentials. Not a Patient')
                return redirect('logout')
        else:
            messages.error(request, 'Invalid username or password')

    return render(request, 'patient-login.html')

@csrf_exempt
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def logoutUser(request):
    logout(request)
    messages.success(request, 'User Logged out')
    return redirect('login')

@csrf_exempt
def patient_register(request):
    page = 'patient-register'
    form = CustomUserCreationForm()

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            # form.save()
            user = form.save(commit=False) # commit=False --> don't save to database yet (we have a chance to modify object)
            user.is_patient = True
            # user.username = user.username.lower()  # lowercase username
            user.save()
            messages.success(request, 'Patient account was created!')

            # After user is created, we can log them in --> login(request, user)
            return redirect('login')

        else:
            messages.error(request, 'An error has occurred during registration')

    context = {'page': page, 'form': form}
    return render(request, 'patient-register.html', context)

@login_required(login_url="login")
def cancel_appointment(request, pk):
    if request.user.is_patient:
        patient = Patient.objects.get(user=request.user)
        appointment = get_object_or_404(Appointment, id=pk, patient=patient)
        if appointment.payment_status != 'VALID':
            appointment.appointment_status = 'cancelled'
            appointment.save()
            messages.success(request, 'Appointment cancelled successfully.')
        else:
            messages.error(request, 'Cannot cancel a paid appointment.')
    return redirect('patient-dashboard')

@csrf_exempt
@login_required(login_url="login")
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def patient_dashboard(request):
    if request.user.is_patient:
        # patient = Patient.objects.get(user_id=pk)
        patient = Patient.objects.get(user=request.user)
        report = Report.objects.filter(patient=patient)
        prescription = Prescription.objects.filter(patient=patient).order_by('-prescription_id')
        base_appointments = (
            Appointment.objects.filter(patient=patient)
            .filter(Q(appointment_status='pending') | Q(appointment_status='confirmed'))
        )

        pending_prescription_appointments = base_appointments.filter(prescriptions__isnull=True)
        finished_appointments = base_appointments.filter(prescriptions__isnull=False).distinct()

        payments = (
            Payment.objects.filter(patient=patient)
            .filter(appointment__in=base_appointments)
            .filter(payment_type='appointment')
            .filter(status='VALID')
        )

        # Test & Payment section: prescriptions that have tests
        prescriptions_with_tests = []
        for pres in prescription:
            tests = Prescription_test.objects.filter(prescription=pres)
            if tests.exists():
                total_amount = 0
                all_paid = True
                for t in tests:
                    try:
                        total_amount += float(t.test_info_price or 0)
                    except (ValueError, TypeError):
                        pass
                    if t.test_info_pay_status != 'Paid':
                        all_paid = False
                # Check if a valid test payment exists for this prescription
                test_payment = Payment.objects.filter(
                    prescription=pres, payment_type='test', status='VALID'
                ).first()
                prescriptions_with_tests.append({
                    'prescription': pres,
                    'tests': tests,
                    'total_amount': total_amount,
                    'all_paid': all_paid,
                    'test_payment': test_payment,
                })

        context = {
            'patient': patient,
            'pending_prescription_appointments': pending_prescription_appointments,
            'finished_appointments': finished_appointments,
            'payments': payments,
            'report': report,
            'prescription': prescription,
            'prescriptions_with_tests': prescriptions_with_tests,
        }
    else:
        return redirect('logout')
        
    return render(request, 'patient-dashboard.html', context)


@csrf_exempt
@login_required(login_url="login")
def pay_prescription_tests(request, pk):
    """Create testCart + testOrder for all unpaid tests in a prescription, then redirect to SSLCommerz."""
    if not request.user.is_patient:
        return redirect('logout')

    patient = Patient.objects.get(user=request.user)
    pres = get_object_or_404(Prescription, prescription_id=pk, patient=patient)
    unpaid_tests = Prescription_test.objects.filter(prescription=pres).exclude(test_info_pay_status='Paid')

    if not unpaid_tests.exists():
        messages.info(request, 'All tests are already paid.')
        return redirect('patient-dashboard')

    # Clear any existing unpurchased carts for this user
    testCart.objects.filter(user=request.user, purchased=False).delete()
    old_orders = testOrder.objects.filter(user=request.user, ordered=False)
    old_orders.delete()

    # Create fresh cart + order
    order = testOrder.objects.create(user=request.user, ordered=False)
    for test in unpaid_tests:
        cart_item = testCart.objects.create(user=request.user, item=test, name=test.test_name or 'test', purchased=False)
        order.orderitems.add(cart_item)
    order.save()

    return redirect('ssl-payment-request-test', pk=patient.patient_id, id=order.id, pk2=pres.prescription_id)


@login_required(login_url="login")
def test_receipt_pdf(request, pk):
    """Generate a PDF receipt for a paid prescription's tests."""
    if not request.user.is_patient:
        return redirect('logout')

    patient = Patient.objects.get(user=request.user)
    pres = get_object_or_404(Prescription, prescription_id=pk, patient=patient)
    tests = Prescription_test.objects.filter(prescription=pres)
    payment = Payment.objects.filter(prescription=pres, payment_type='test', status='VALID').first()

    if not payment:
        messages.error(request, 'No valid payment found for these tests.')
        return redirect('patient-dashboard')

    total_amount = 0
    for t in tests:
        try:
            total_amount += float(t.test_info_price or 0)
        except (ValueError, TypeError):
            pass

    context = {
        'patient': patient,
        'prescription': pres,
        'tests': tests,
        'payment': payment,
        'total_amount': total_amount,
        'current_date': datetime.date.today(),
    }
    template = get_template('test_receipt_pdf.html')
    html = template.render(context)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
    if not pdf.err:
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename=test_receipt.pdf'
        return response
    return HttpResponse("Error generating PDF", status=500)


# def profile_settings(request):
#     if request.user.is_patient:
#         # patient = Patient.objects.get(user_id=pk)
#         patient = Patient.objects.get(user=request.user)
#         form = PatientForm(instance=patient)  

#         if request.method == 'POST':
#             form = PatientForm(request.POST, request.FILES,instance=patient)  
#             if form.is_valid():
#                 form.save()
#                 return redirect('patient-dashboard')
#             else:
#                 form = PatientForm()
#     else:
#         redirect('logout')

#     context = {'patient': patient, 'form': form}
#     return render(request, 'profile-settings.html', context)

@csrf_exempt
@login_required(login_url="login")
def profile_settings(request):
    if request.user.is_patient:
        # patient = Patient.objects.get(user_id=pk)
        patient = Patient.objects.get(user=request.user)
        old_featured_image = patient.featured_image
        
        if request.method == 'GET':
            context = {'patient': patient}
            return render(request, 'profile-settings.html', context)
        elif request.method == 'POST':
            if 'featured_image' in request.FILES:
                featured_image = request.FILES['featured_image']
            else:
                featured_image = old_featured_image
                
            name = request.POST.get('name')
            dob = request.POST.get('dob')
            age = request.POST.get('age')
            blood_group = request.POST.get('blood_group')
            phone_number = request.POST.get('phone_number')
            address = request.POST.get('address')
            nid = request.POST.get('nid')
            history = request.POST.get('history')
            
            patient.name = name
            patient.age = age
            patient.phone_number = phone_number
            patient.address = address
            patient.blood_group = blood_group
            patient.history = history
            patient.dob = dob
            patient.nid = nid
            patient.featured_image = featured_image
            
            patient.save()
            
            messages.success(request, 'Profile Settings Changed!')
            
            return redirect('patient-dashboard')
    else:
        redirect('logout')  
        
@csrf_exempt
@login_required(login_url="login")
def search(request):
    if request.user.is_authenticated and request.user.is_patient:
        # patient = Patient.objects.get(user_id=pk)
        patient = Patient.objects.get(user=request.user)

        doctors, search_query = searchDoctors(request)

        per_page_options = [5, 10, 20]
        try:
            per_page = int(request.GET.get('per_page', per_page_options[0]))
        except (TypeError, ValueError):
            per_page = per_page_options[0]
        if per_page not in per_page_options:
            per_page = per_page_options[0]

        custom_range, doctors = paginateDoctors(request, doctors, per_page)

        query_params = request.GET.copy()
        if 'page' in query_params:
            del query_params['page']
        querystring = query_params.urlencode()

        context = {
            'patient': patient,
            'doctors': doctors,
            'search_query': search_query,
            'custom_range': custom_range,
            'per_page': per_page,
            'per_page_options': per_page_options,
            'querystring': querystring,
        }
        return render(request, 'search.html', context)
    else:
        logout(request)
        messages.error(request, 'Not Authorized')
        return render(request, 'patient-login.html')    
    

def checkout_payment(request):
    return render(request, 'checkout.html')

@csrf_exempt
@login_required(login_url="login")
def multiple_hospital(request):
    
    if request.user.is_authenticated: 
        
        if request.user.is_patient:
            # patient = Patient.objects.get(user_id=pk)
            patient = Patient.objects.get(user=request.user)
            doctors = Doctor_Information.objects.filter(register_status='Accepted')
            hospitals = Hospital_Information.objects.all()
            
            hospitals, search_query = searchHospitals(request)
            
            # PAGINATION ADDED TO MULTIPLE HOSPITALS
            custom_range, hospitals = paginateHospitals(request, hospitals, 3)
        
            context = {'patient': patient, 'doctors': doctors, 'hospitals': hospitals, 'search_query': search_query, 'custom_range': custom_range}
            return render(request, 'multiple-hospital.html', context)
        
        elif request.user.is_doctor:
            doctor = Doctor_Information.objects.get(user=request.user)
            hospitals = Hospital_Information.objects.all()
            
            hospitals, search_query = searchHospitals(request)
            
            context = {'doctor': doctor, 'hospitals': hospitals, 'search_query': search_query}
            return render(request, 'multiple-hospital.html', context)
    else:
        logout(request)
        messages.error(request, 'Not Authorized')
        return render(request, 'patient-login.html') 
    
@csrf_exempt    
@login_required(login_url="login")
def hospital_profile(request, pk):
    
    if request.user.is_authenticated: 
        
        if request.user.is_patient:
            patient = Patient.objects.get(user=request.user)
            doctors = Doctor_Information.objects.filter(register_status='Accepted')
            hospitals = Hospital_Information.objects.get(hospital_id=pk)
        
            departments = hospital_department.objects.filter(hospital=hospitals)
            specializations = specialization.objects.filter(hospital=hospitals)
            services = service.objects.filter(hospital=hospitals)
            
            # department_list = None
            # for d in departments:
            #     vald = d.hospital_department_name
            #     vald = re.sub("'", "", vald)
            #     vald = vald.replace("[", "")
            #     vald = vald.replace("]", "")
            #     vald = vald.replace(",", "")
            #     department_list = vald.split()
            
            context = {'patient': patient, 'doctors': doctors, 'hospitals': hospitals, 'departments': departments, 'specializations': specializations, 'services': services}
            return render(request, 'hospital-profile.html', context)
        
        elif request.user.is_doctor:
           
            doctor = Doctor_Information.objects.get(user=request.user)
            hospitals = Hospital_Information.objects.get(hospital_id=pk)
            
            departments = hospital_department.objects.filter(hospital=hospitals)
            specializations = specialization.objects.filter(hospital=hospitals)
            services = service.objects.filter(hospital=hospitals)
            
            context = {'doctor': doctor, 'hospitals': hospitals, 'departments': departments, 'specializations': specializations, 'services': services}
            return render(request, 'hospital-profile.html', context)
    else:
        logout(request)
        messages.error(request, 'Not Authorized')
        return render(request, 'patient-login.html') 
    
    
def data_table(request):
    return render(request, 'data-table.html')

@csrf_exempt
@login_required(login_url="login")
def hospital_department_list(request, pk):
    if request.user.is_authenticated: 
        
        if request.user.is_patient:
            # patient = Patient.objects.get(user_id=pk)
            patient = Patient.objects.get(user=request.user)
            doctors = Doctor_Information.objects.filter(register_status='Accepted')
            
            hospitals = Hospital_Information.objects.get(hospital_id=pk)
            departments = hospital_department.objects.filter(hospital=hospitals)
        
            context = {'patient': patient, 'doctors': doctors, 'hospitals': hospitals, 'departments': departments}
            return render(request, 'hospital-department.html', context)
        
        elif request.user.is_doctor:
            doctor = Doctor_Information.objects.get(user=request.user)
            hospitals = Hospital_Information.objects.get(hospital_id=pk)
            departments = hospital_department.objects.filter(hospital=hospitals)
            
            context = {'doctor': doctor, 'hospitals': hospitals, 'departments': departments}
            return render(request, 'hospital-department.html', context)
    else:
        logout(request)
        messages.info(request, 'Not Authorized')
        return render(request, 'patient-login.html')

@csrf_exempt
@login_required(login_url="login")
def hospital_doctor_list(request, pk):
    if request.user.is_authenticated and request.user.is_patient:
        # patient = Patient.objects.get(user_id=pk)
        patient = Patient.objects.get(user=request.user)
        departments = hospital_department.objects.get(hospital_department_id=pk)
        doctors, search_query = searchDepartmentDoctors(request, pk)

        per_page_options = [5, 10, 20]
        try:
            per_page = int(request.GET.get('per_page', per_page_options[0]))
        except (TypeError, ValueError):
            per_page = per_page_options[0]
        if per_page not in per_page_options:
            per_page = per_page_options[0]

        custom_range, doctors = paginateDoctors(request, doctors, per_page)

        query_params = request.GET.copy()
        if 'page' in query_params:
            del query_params['page']
        querystring = query_params.urlencode()
        
        context = {
            'patient': patient,
            'department': departments,
            'doctors': doctors,
            'search_query': search_query,
            'pk_id': pk,
            'custom_range': custom_range,
            'per_page': per_page,
            'per_page_options': per_page_options,
            'querystring': querystring,
        }
        return render(request, 'hospital-doctor-list.html', context)

    elif request.user.is_authenticated and request.user.is_doctor:
        # patient = Patient.objects.get(user_id=pk)
        
        doctor = Doctor_Information.objects.get(user=request.user)
        departments = hospital_department.objects.get(hospital_department_id=pk)
        doctors, search_query = searchDepartmentDoctors(request, pk)

        per_page_options = [5, 10, 20]
        try:
            per_page = int(request.GET.get('per_page', per_page_options[0]))
        except (TypeError, ValueError):
            per_page = per_page_options[0]
        if per_page not in per_page_options:
            per_page = per_page_options[0]

        custom_range, doctors = paginateDoctors(request, doctors, per_page)

        query_params = request.GET.copy()
        if 'page' in query_params:
            del query_params['page']
        querystring = query_params.urlencode()
        
        context = {
            'doctor': doctor,
            'department': departments,
            'doctors': doctors,
            'search_query': search_query,
            'pk_id': pk,
            'custom_range': custom_range,
            'per_page': per_page,
            'per_page_options': per_page_options,
            'querystring': querystring,
        }
        return render(request, 'hospital-doctor-list.html', context)
    else:
        logout(request)
        messages.error(request, 'Not Authorized')
        return render(request, 'patient-login.html')   
    


@csrf_exempt
@login_required(login_url="login")
def hospital_doctor_register(request, pk):
    messages.error(request, 'Hospital assignment for doctors is handled by the hospital admin.')
    if request.user.is_authenticated and request.user.is_doctor:
        return redirect('doctor-dashboard')
    return redirect('doctor-login')
    
   
def testing(request):
    # hospitals = Hospital_Information.objects.get(hospital_id=1)
    test = "test"
    context = {'test': test}
    return render(request, 'testing.html', context)

@csrf_exempt
@login_required(login_url="login")
def view_report(request,pk):
    if request.user.is_patient:
        patient = Patient.objects.get(user=request.user)
        report = Report.objects.filter(report_id=pk)
        specimen = Specimen.objects.filter(report__in=report)
        test = Test.objects.filter(report__in=report)

        # current_date = datetime.date.today()
        context = {'patient':patient,'report':report,'test':test,'specimen':specimen}
        return render(request, 'view-report.html',context)
    else:
        redirect('logout') 


def test_cart(request):
    return render(request, 'test-cart.html')

@csrf_exempt
@login_required(login_url="login")
def test_single(request,pk):
     if request.user.is_authenticated and request.user.is_patient:
         
        patient = Patient.objects.get(user=request.user)
        Perscription_test = Perscription_test.objects.get(test_id=pk)
        carts = testCart.objects.filter(user=request.user, purchased=False)
        
        context = {'patient': patient, 'carts': carts, 'Perscription_test': Perscription_test}
        return render(request, 'test-cart.html',context)
     else:
        logout(request)
        messages.info(request, 'Not Authorized')
        return render(request, 'patient-login.html')  

@csrf_exempt
@login_required(login_url="login")
def test_add_to_cart(request, pk, pk2):
    if request.user.is_authenticated and request.user.is_patient:
         
        patient = Patient.objects.get(user=request.user)
        test_information = Test_Information.objects.get(test_id=pk2)
        prescription = Prescription.objects.filter(prescription_id=pk)

        item = get_object_or_404(Prescription_test, test_info_id=pk2,prescription_id=pk)
        order_item = testCart.objects.get_or_create(item=item, user=request.user, purchased=False)
        order_qs = testOrder.objects.filter(user=request.user, ordered=False)

        if order_qs.exists():
            order = order_qs[0]
            order.orderitems.add(order_item[0])
            # messages.info(request, "This test is added to your cart!")
            return redirect("prescription-view", pk=pk)
        else:
            order = testOrder(user=request.user)
            order.save()
            order.orderitems.add(order_item[0])
            return redirect("prescription-view", pk=pk)

        context = {'patient': patient,'prescription_test': prescription_tests,'prescription':prescription,'prescription_medicine':prescription_medicine,'test_information':test_information}
        return render(request, 'prescription-view.html', context)
    else:
        logout(request)
        messages.info(request, 'Not Authorized')
        return render(request, 'patient-login.html')  

@csrf_exempt
@login_required(login_url="login")
def test_cart(request, pk):
    if request.user.is_authenticated and request.user.is_patient:
        # prescription = Prescription.objects.filter(prescription_id=pk)
        
        prescription = Prescription.objects.filter(prescription_id=pk)
        
        patient = Patient.objects.get(user=request.user)
        prescription_test = Prescription_test.objects.all()
        test_carts = testCart.objects.filter(user=request.user, purchased=False)
        test_orders = testOrder.objects.filter(user=request.user, ordered=False)
        
        if test_carts.exists() and test_orders.exists():
            test_order = test_orders[0]
            
            context = {'test_carts': test_carts,'test_order': test_order, 'patient': patient, 'prescription_test':prescription_test, 'prescription_id':pk}
            return render(request, 'test-cart.html', context)
        else:
            # messages.warning(request, "You don't have any test in your cart!")
            context = {'patient': patient,'prescription_test':prescription_test}
            return render(request, 'prescription-view.html', context)
    else:
        logout(request)
        messages.info(request, 'Not Authorized')
        return render(request, 'patient-login.html') 

@csrf_exempt
@login_required(login_url="login")
def test_remove_cart(request, pk):
    if request.user.is_authenticated and request.user.is_patient:
        item = Prescription_test.objects.get(test_id=pk)

        patient = Patient.objects.get(user=request.user)
        prescription = Prescription.objects.filter(prescription_id=pk)
        prescription_medicine = Prescription_medicine.objects.filter(prescription__in=prescription)
        prescription_test = Prescription_test.objects.filter(prescription__in=prescription)
        test_carts = testCart.objects.filter(user=request.user, purchased=False)
        
        # item = get_object_or_404(test, pk=pk)
        test_order_qs = testOrder.objects.filter(user=request.user, ordered=False)
        if test_order_qs.exists():
            test_order = test_order_qs[0]
            if test_order.orderitems.filter(item=item).exists():
                test_order_item = testCart.objects.filter(item=item, user=request.user, purchased=False)[0]
                test_order.orderitems.remove(test_order_item)
                test_order_item.delete()
                # messages.warning(request, "This test was remove from your cart!")
                context = {'test_carts': test_carts,'test_order': test_order,'patient': patient,'prescription_id':pk}
                return render(request, 'test-cart.html', context)
            else:
                # messages.info(request, "This test was not in your cart")
                context = {'patient': patient,'test': item,'prescription':prescription,'prescription_medicine':prescription_medicine,'prescription_test':prescription_test}
                return render(request, 'prescription-view.html', context)
        else:
            # messages.info(request, "You don't have an active order")
            context = {'patient': patient,'test': item,'prescription':prescription,'prescription_medicine':prescription_medicine,'prescription_test':prescription_test}
            return redirect('prescription-view', pk=prescription.prescription_id)
    else:
        logout(request)
        messages.info(request, 'Not Authorized')
        return render(request, 'patient-login.html') 

@csrf_exempt
def prescription_view(request,pk):
      if request.user.is_patient:
        patient = Patient.objects.get(user=request.user)
        prescription = Prescription.objects.filter(prescription_id=pk)
        prescription_medicine = Prescription_medicine.objects.filter(prescription__in=prescription)
        prescription_test = Prescription_test.objects.filter(prescription__in=prescription)

        context = {'patient':patient,'prescription':prescription,'prescription_test':prescription_test,'prescription_medicine':prescription_medicine}
        return render(request, 'prescription-view.html',context)
      else:
         redirect('logout') 

@csrf_exempt
def render_to_pdf(template_src, context_dict={}):
    template=get_template(template_src)
    html=template.render(context_dict)
    result=BytesIO()
    pres_pdf=pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
    if not pres_pdf.err:
        return HttpResponse(result.getvalue(),content_type="aplication/pres_pdf")
    return None


# def prescription_pdf(request,pk):
#  if request.user.is_patient:
#     patient = Patient.objects.get(user=request.user)
#     prescription = Prescription.objects.get(prescription_id=pk)
#     perscription_medicine = Perscription_medicine.objects.filter(prescription=prescription)
#     perscription_test = Perscription_test.objects.filter(prescription=prescription)
#     current_date = datetime.date.today()
#     context={'patient':patient,'current_date' : current_date,'prescription':prescription,'perscription_test':perscription_test,'perscription_medicine':perscription_medicine}
#     pdf=render_to_pdf('prescription_pdf.html', context)
#     if pdf:
#         response=HttpResponse(pdf, content_type='application/pdf')
#         content="inline; filename=report.pdf"
#         # response['Content-Disposition']= content
#         return response
#     return HttpResponse("Not Found")

@csrf_exempt
def prescription_pdf(request,pk):
 if request.user.is_patient:
    patient = Patient.objects.get(user=request.user)
    prescription = Prescription.objects.get(prescription_id=pk)
    prescription_medicine = Prescription_medicine.objects.filter(prescription=prescription)
    prescription_test = Prescription_test.objects.filter(prescription=prescription)
    # current_date = datetime.date.today()
    context={'patient':patient,'prescription':prescription,'prescription_test':prescription_test,'prescription_medicine':prescription_medicine}
    pres_pdf=render_to_pdf('prescription_pdf.html', context)
    if pres_pdf:
        response=HttpResponse(pres_pdf, content_type='application/pres_pdf')
        content="inline; filename=prescription.pdf"
        response['Content-Disposition']= content
        return response
    return HttpResponse("Not Found")

@csrf_exempt
@login_required(login_url="login")
def delete_prescription(request,pk):
    if request.user.is_authenticated and request.user.is_patient:
        prescription = Prescription.objects.get(prescription_id=pk)
        prescription.delete()
        messages.success(request, 'Prescription Deleted')
        return redirect('patient-dashboard')
    else:
        logout(request)
        messages.error(request, 'Not Authorized')
        return render(request, 'patient-login.html')

@csrf_exempt
@login_required(login_url="login")
def delete_report(request,pk):
    if request.user.is_authenticated and request.user.is_patient:
        report = Report.objects.get(report_id=pk)
        report.delete()
        messages.success(request, 'Report Deleted')
        return redirect('patient-dashboard')
    else:
        logout(request)
        messages.error(request, 'Not Authorized')
        return render(request, 'patient-login.html')

@csrf_exempt
@receiver(user_logged_in)
def got_online(sender, user, request, **kwargs):    
    user.login_status = True
    user.save()

@csrf_exempt
@receiver(user_logged_out)
def got_offline(sender, user, request, **kwargs):   
    user.login_status = False
    user.save()
    



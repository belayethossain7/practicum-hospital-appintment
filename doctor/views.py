import email
from email import message
from multiprocessing import context
from turtle import title
from django.shortcuts import render, redirect, get_object_or_404
# from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from hospital_admin.views import prescription_list
from .forms import DoctorUserCreationForm, DoctorForm
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.cache import cache_control
from hospital.models import User, Patient
from hospital_admin.models import Admin_Information,Clinical_Laboratory_Technician
from .models import Doctor_Information, Appointment, Education, Experience, Prescription_medicine, Report,Specimen,Test, Prescription_test, Prescription, Doctor_review
from hospital_admin.models import Admin_Information,Clinical_Laboratory_Technician, Test_Information
from .models import Doctor_Information, Appointment, Education, Experience, Prescription_medicine, Report,Specimen,Test, Prescription_test, Prescription
from django.db.models import Q, Count, Exists, OuterRef, Subquery
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
import random
import string
from datetime import datetime, timedelta
import datetime
import re
from django.core.mail import BadHeaderError, send_mail
from django.conf import settings
import smtplib
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.http import JsonResponse
from django.utils.html import strip_tags
from django.urls import reverse
from django.utils import timezone
from io import BytesIO
from urllib import response
from django.shortcuts import render
from django.template.loader import get_template
from django.http import HttpResponse
from xhtml2pdf import pisa
from .models import Report
from django.views.decorators.csrf import csrf_exempt
from sslcommerz.models import Payment
import time


from .slots import (
    format_time_display,
    get_doctor_booked_time_strings,
    is_time_in_slot_window,
    is_valid_slot_increment,
    parse_appointment_date,
    parse_appointment_time,
)


@csrf_exempt
def booking_slots(request, pk):
    """Return booked time slots for a doctor on a given date.

    Query params:
      - date: accepts YYYY-MM-DD (native <input type=date>) or MM/DD/YYYY (dateDropper)
    """
    if request.method != 'GET':
        return JsonResponse({'detail': 'Method not allowed'}, status=405)

    doctor = Doctor_Information.objects.get(doctor_id=pk)
    date_str = request.GET.get('date', '')

    try:
        date_value = parse_appointment_date(date_str)
    except ValueError as exc:
        return JsonResponse({'detail': str(exc)}, status=400)

    booked = sorted(get_doctor_booked_time_strings(doctor, date_value))

    now_local = timezone.localtime(timezone.now())
    now_minutes = (now_local.hour * 60) + now_local.minute

    return JsonResponse({
        'date': str(date_value),
        'booked': booked,
        'server_today': str(now_local.date()),
        'server_now_minutes': now_minutes,
    })

# Create your views here.

def generate_random_string():
    N = 8
    string_var = ""
    string_var = ''.join(random.choices(
        string.ascii_uppercase + string.digits, k=N))
    return string_var

@csrf_exempt
@login_required(login_url="doctor-login")
def doctor_change_password(request,pk):
    doctor = Doctor_Information.objects.get(user_id=pk)
    context={'doctor':doctor}
    if request.method == "POST":
        
        new_password = request.POST["new_password"]
        confirm_password = request.POST["confirm_password"]
        if new_password == confirm_password:
            
            request.user.set_password(new_password)
            request.user.save()
            messages.success(request,"Password Changed Successfully")
            return redirect("doctor-dashboard")
            
        else:
            messages.error(request,"New Password and Confirm Password is not same")
            return redirect("change-password",pk)
    return render(request, 'doctor-change-password.html',context)

@csrf_exempt
@login_required(login_url="doctor-login")
def schedule_timings(request):
    doctor = Doctor_Information.objects.get(user=request.user)
    context = {'doctor': doctor}
    
    return render(request, 'schedule-timings.html', context)

@csrf_exempt
@login_required(login_url="doctor-login")
def patient_id(request):
    return render(request, 'patient-id.html')

@csrf_exempt
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def logoutDoctor(request):
    user = User.objects.get(id=request.user.id)
    if user.is_doctor:
        user.login_status == "offline"
        user.save()
        logout(request)
    
    messages.success(request, 'User Logged out')
    return render(request,'doctor-login.html')

@csrf_exempt
def doctor_register(request):
    messages.error(request, 'Doctor registration is disabled. Please contact the hospital admin to create your account.')
    return redirect('doctor-login')

@csrf_exempt
def doctor_login(request):
    # page = 'patient_login'
    if request.method == 'GET':
        return render(request, 'doctor-login.html')
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
            if request.user.is_doctor:
                # user.login_status = "online"
                # user.save()
                messages.success(request, 'Welcome Doctor!')
                return redirect('doctor-dashboard')
            else:
                messages.error(request, 'Invalid credentials. Not a Doctor')
                return redirect('doctor-logout')   
        else:
            messages.error(request, 'Invalid username or password')
            
    return render(request, 'doctor-login.html')

@csrf_exempt
@login_required(login_url="doctor-login")
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def doctor_dashboard(request):
        if request.user.is_authenticated:    
            if request.user.is_doctor:
                # doctor = Doctor_Information.objects.get(user_id=pk)
                doctor = Doctor_Information.objects.get(user=request.user)
                # appointments = Appointment.objects.filter(doctor=doctor).filter(Q(appointment_status='pending') | Q(appointment_status='confirmed'))
                current_date = datetime.date.today()
                current_date_str = str(current_date)  
                today_appointments = Appointment.objects.filter(date=current_date_str).filter(doctor=doctor).filter(appointment_status='confirmed')
                
                next_date = current_date + datetime.timedelta(days=1) # next days date 
                next_date_str = str(next_date)  
                next_days_appointment = Appointment.objects.filter(date=next_date_str).filter(doctor=doctor).filter(Q(appointment_status='pending') | Q(appointment_status='confirmed')).count()
                
                today_patient_count = Appointment.objects.filter(date=current_date_str).filter(doctor=doctor).annotate(count=Count('patient'))
                total_appointments_count = Appointment.objects.filter(doctor=doctor).annotate(count=Count('id'))
            else:
                return redirect('doctor-logout')
            
            context = {'doctor': doctor, 'today_appointments': today_appointments, 'today_patient_count': today_patient_count, 'total_appointments_count': total_appointments_count, 'next_days_appointment': next_days_appointment, 'current_date': current_date_str, 'next_date': next_date_str}
            return render(request, 'doctor-dashboard.html', context)
        else:
            return redirect('doctor-login')
 
@csrf_exempt
@login_required(login_url="doctor-login")
def appointments(request):
    doctor = Doctor_Information.objects.get(user=request.user)
    base = Appointment.objects.filter(doctor=doctor, appointment_status='confirmed')

    presc_exists = Prescription.objects.filter(appointment=OuterRef('pk'))
    presc_id = Prescription.objects.filter(appointment=OuterRef('pk')).values('prescription_id')[:1]

    base = base.annotate(
        has_prescription=Exists(presc_exists),
        prescription_id=Subquery(presc_id),
    )

    open_appointments = base.filter(has_prescription=False).order_by('date', 'time')
    finished_appointments = base.filter(has_prescription=True).order_by('-date', '-time')

    context = {
        'doctor': doctor,
        'open_appointments': open_appointments,
        'finished_appointments': finished_appointments,
    }
    return render(request, 'appointments.html', context) 


@login_required(login_url="doctor-login")
def add_appointment_payment(request, pk):
    if request.method != 'POST':
        return redirect('appointments')

    doctor = Doctor_Information.objects.get(user=request.user)
    appointment = get_object_or_404(
        Appointment,
        pk=pk,
        doctor=doctor,
    )

    if appointment.appointment_status == 'cancelled':
        messages.error(request, 'Cannot add payment: appointment is cancelled.')
        return redirect('appointments')

    if Payment.objects.filter(
        appointment=appointment,
        patient=appointment.patient,
        payment_type='appointment',
        status='VALID',
    ).exists():
        if str(appointment.payment_status).strip().upper() != 'VALID':
            appointment.payment_status = 'VALID'
            appointment.save(update_fields=['payment_status'])
        messages.info(request, 'Payment is already recorded as paid.')
        return redirect('appointments')

    if str(appointment.payment_status).strip().upper() == 'VALID':
        messages.info(request, 'Payment is already marked as paid.')
        return redirect('appointments')

    if appointment.appointment_type == 'checkup':
        amount = doctor.consultation_fee
        consulation_fee = str(amount) if amount is not None else ''
        report_fee = ''
    else:
        amount = doctor.report_fee
        consulation_fee = ''
        report_fee = str(amount) if amount is not None else ''

    if amount is None:
        messages.error(request, 'Cannot add payment: appointment fee is not set for this doctor.')
        return redirect('appointments')

    offline_tx = f"OFFLINE-{appointment.id}-{int(time.time())}"
    now_str = str(datetime.datetime.now())

    Payment.objects.create(
        patient=appointment.patient,
        appointment=appointment,
        payment_type='appointment',
        name=getattr(appointment.patient, 'name', ''),
        email=getattr(appointment.patient, 'email', ''),
        phone=getattr(appointment.patient, 'phone_number', ''),
        transaction_id=offline_tx,
        val_transaction_id=offline_tx,
        currency_amount=str(amount) if amount is not None else '',
        consulation_fee=consulation_fee,
        report_fee=report_fee,
        status='VALID',
        transaction_date=now_str,
        currency='BDT',
        card_type='OFFLINE',
    )

    appointment.payment_status = 'VALID'
    appointment.transaction_id = offline_tx
    appointment.save(update_fields=['payment_status', 'transaction_id'])

    messages.success(request, 'Payment added successfully.')
    return redirect('appointments')
 
@csrf_exempt        
@login_required(login_url="doctor-login")
def accept_appointment(request, pk):
    appointment = Appointment.objects.get(id=pk)
    appointment.appointment_status = 'confirmed'
    appointment.save()

    # Ensure the slot is exclusive: cancel any competing pending requests.
    try:
        confirmed_time = parse_appointment_time(appointment.time)
    except ValueError:
        confirmed_time = None

    competing = Appointment.objects.filter(
        doctor=appointment.doctor,
        date=appointment.date,
        appointment_status='pending',
    ).exclude(pk=appointment.pk)

    if confirmed_time is None:
        competing.filter(time=appointment.time).update(appointment_status='cancelled')
    else:
        confirmed_display = format_time_display(confirmed_time)
        for other in competing:
            try:
                other_display = format_time_display(parse_appointment_time(other.time))
            except ValueError:
                other_display = str(other.time).strip()
            if other_display == confirmed_display:
                other.appointment_status = 'cancelled'
                other.save(update_fields=['appointment_status'])
    
    # Mailtrap
    
    patient_email = appointment.patient.email
    patient_name = appointment.patient.name
    patient_username = appointment.patient.username
    patient_serial_number = appointment.patient.serial_number
    doctor_name = appointment.doctor.name

    appointment_serial_number = appointment.serial_number
    appointment_date = appointment.date
    appointment_time = appointment.time
    appointment_status = appointment.appointment_status
    
    subject = "Appointment Acceptance Email"
    
    values = {
            "email":patient_email,
            "name":patient_name,
            "username":patient_username,
            "serial_number":patient_serial_number,
            "doctor_name":doctor_name,
            "appointment_serial_num":appointment_serial_number,
            "appointment_date":appointment_date,
            "appointment_time":appointment_time,
            "appointment_status":appointment_status,
    }
    
    html_message = render_to_string('appointment_accept_mail.html', {'values': values})
    plain_message = strip_tags(html_message)

    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None) or getattr(settings, 'EMAIL_HOST_USER', None)
    try:
        send_mail(subject, plain_message, from_email, [patient_email], html_message=html_message, fail_silently=False)
    except BadHeaderError:
        return HttpResponse('Invalid header found')
    except (smtplib.SMTPException, OSError) as exc:
        # Appointment is already confirmed; don't fail the flow due to email issues.
        messages.warning(request, f'Appointment accepted, but email could not be sent ({type(exc).__name__}).')
    
    messages.success(request, 'Appointment Accepted')
    
    return redirect('doctor-dashboard')

@csrf_exempt
@login_required(login_url="doctor-login")
def reject_appointment(request, pk):
    appointment = Appointment.objects.get(id=pk)
    appointment.appointment_status = 'cancelled'
    appointment.save()
    
    # Mailtrap
    
    patient_email = appointment.patient.email
    patient_name = appointment.patient.name
    doctor_name = appointment.doctor.name

    subject = "Appointment Rejection Email"
    
    values = {
            "email":patient_email,
            "name":patient_name,
            "doctor_name":doctor_name,
    }
    
    html_message = render_to_string('appointment_reject_mail.html', {'values': values})
    plain_message = strip_tags(html_message)

    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None) or getattr(settings, 'EMAIL_HOST_USER', None)
    try:
        send_mail(subject, plain_message, from_email, [patient_email], html_message=html_message, fail_silently=False)
    except BadHeaderError:
        return HttpResponse('Invalid header found')
    except (smtplib.SMTPException, OSError) as exc:
        messages.warning(request, f'Appointment rejected, but email could not be sent ({type(exc).__name__}).')
    
    messages.error(request, 'Appointment Rejected')
    
    return redirect('doctor-dashboard')


#         end_year = doctor.end_year
#         end_year = re.sub("'", "", end_year)
#         end_year = end_year.replace("[", "")
#         end_year = end_year.replace("]", "")
#         end_year = end_year.replace(",", "")
#         end_year_array = end_year.split()       
#         experience = zip(work_place_array, designation_array, start_year_array, end_year_array)

@csrf_exempt
@login_required(login_url="doctor-login")
def doctor_profile(request, pk):
    # request.user --> get logged in user
    if request.user.is_patient:
        patient = request.user.patient
    else:
        patient = None
    
    doctor = Doctor_Information.objects.get(doctor_id=pk)
    # doctor = Doctor_Information.objects.filter(doctor_id=pk).order_by('-doctor_id')
    
    educations = Education.objects.filter(doctor=doctor).order_by('-year_of_completion')
    experiences = Experience.objects.filter(doctor=doctor).order_by('-from_year','-to_year')
    doctor_review = Doctor_review.objects.filter(doctor=doctor)
            
    context = {'doctor': doctor, 'patient': patient, 'educations': educations, 'experiences': experiences, 'doctor_review': doctor_review}
    return render(request, 'doctor-profile.html', context)

@csrf_exempt
@login_required(login_url="doctor-login")
def delete_education(request, pk):
    if request.user.is_doctor:
        doctor = Doctor_Information.objects.get(user=request.user)
        
        educations = Education.objects.get(education_id=pk)
        educations.delete()
        
        messages.success(request, 'Education Deleted')
        return redirect('doctor-profile-settings')

@csrf_exempt  
@login_required(login_url="doctor-login")
def delete_experience(request, pk):
    if request.user.is_doctor:
        doctor = Doctor_Information.objects.get(user=request.user)
        
        experiences = Experience.objects.get(experience_id=pk)
        experiences.delete()
        
        messages.success(request, 'Experience Deleted')
        return redirect('doctor-profile-settings')
      
@csrf_exempt      
@login_required(login_url="doctor-login")
def doctor_profile_settings(request):
    # profile_Settings.js
    if request.user.is_doctor:
        doctor = Doctor_Information.objects.get(user=request.user)
        old_featured_image = doctor.featured_image
        

        if request.method == 'GET':
            educations = Education.objects.filter(doctor=doctor)
            experiences = Experience.objects.filter(doctor=doctor)
                    
            context = {'doctor': doctor, 'educations': educations, 'experiences': experiences}
            return render(request, 'doctor-profile-settings.html', context)
        elif request.method == 'POST':
            if 'featured_image' in request.FILES:
                featured_image = request.FILES['featured_image']
            else:
                featured_image = old_featured_image
                
            name = request.POST.get('name')
            number = request.POST.get('number')
            gender = request.POST.get('gender')
            dob = request.POST.get('dob')
            description = request.POST.get('description')
            consultation_fee = request.POST.get('consultation_fee')
            report_fee = request.POST.get('report_fee')
            nid = request.POST.get('nid')
            visit_hour = request.POST.get('visit_hour')
            
            degree = request.POST.getlist('degree')
            institute = request.POST.getlist('institute')
            year_complete = request.POST.getlist('year_complete')
            hospital_name = request.POST.getlist('hospital_name')     
            start_year= request.POST.getlist('from')
            end_year = request.POST.getlist('to')
            designation = request.POST.getlist('designation')

            doctor.name = name
            doctor.visiting_hour = visit_hour
            doctor.nid = nid
            doctor.gender = gender
            doctor.featured_image = featured_image
            doctor.phone_number = number
            #doctor.visiting_hour
            doctor.consultation_fee = consultation_fee
            doctor.report_fee = report_fee
            doctor.description = description
            doctor.dob = dob
            
            doctor.save()
            
            # Education
            for i in range(len(degree)):
                education = Education(doctor=doctor)
                education.degree = degree[i]
                education.institute = institute[i]
                education.year_of_completion = year_complete[i]
                education.save()

            # Experience
            for i in range(len(hospital_name)):
                experience = Experience(doctor=doctor)
                experience.work_place_name = hospital_name[i]
                experience.from_year = start_year[i]
                experience.to_year = end_year[i]
                experience.designation = designation[i]
                experience.save()
      
            # context = {'degree': degree}
            messages.success(request, 'Profile Updated')
            return redirect('doctor-dashboard')
    else:
        redirect('doctor-logout')
               
@csrf_exempt    
@login_required(login_url="login")      
def booking_success(request):
    return render(request, 'booking-success.html')

@csrf_exempt
@login_required(login_url="login")
def booking(request, pk):
    patient = request.user.patient
    doctor = Doctor_Information.objects.get(doctor_id=pk)

    if request.method == 'POST':
        appointment = Appointment(patient=patient, doctor=doctor)
        date = request.POST.get('appoint_date', '')
        time = request.POST.get('appoint_time', '')
        appointment_type = request.POST['appointment_type']
        message = request.POST.get('message', '')

        try:
            parsed_date = parse_appointment_date(date)
        except ValueError:
            messages.error(request, 'Invalid appointment date.')
            return render(request, 'booking.html', {'patient': patient, 'doctor': doctor})

        today_local = timezone.localdate()
        if parsed_date < today_local:
            messages.error(request, 'You cannot book an appointment in the past.')
            return render(request, 'booking.html', {'patient': patient, 'doctor': doctor})

        try:
            parsed_time = parse_appointment_time(time)
        except ValueError:
            messages.error(request, 'Invalid appointment time.')
            return render(request, 'booking.html', {'patient': patient, 'doctor': doctor})

        if not is_time_in_slot_window(parsed_time) or not is_valid_slot_increment(parsed_time):
            messages.error(request, 'Please select a 30-minute slot between 10:00 AM and 4:00 PM.')
            return render(request, 'booking.html', {'patient': patient, 'doctor': doctor})

        if parsed_date == today_local:
            now_local_time = timezone.localtime(timezone.now()).time()
            # Do not allow booking for a time slot that has already started or passed.
            if parsed_time <= now_local_time:
                messages.error(request, 'Please select a future time slot for today.')
                return render(request, 'booking.html', {'patient': patient, 'doctor': doctor})

        normalized_time = format_time_display(parsed_time)

        # Block double-booking for this doctor/date/time (pending or confirmed).
        if normalized_time in get_doctor_booked_time_strings(doctor, parsed_date):
            messages.error(request, 'This time slot is already booked. Please choose another slot.')
            return render(request, 'booking.html', {'patient': patient, 'doctor': doctor})

        appointment.date = parsed_date
        appointment.time = normalized_time
        appointment.appointment_status = 'confirmed'
        appointment.serial_number = generate_random_string()
        appointment.appointment_type = appointment_type
        appointment.message = message
        appointment.save()

        # Email patient immediately (appointment is confirmed on submit)
        patient_email = appointment.patient.email
        patient_name = appointment.patient.name
        patient_username = appointment.patient.username
        patient_serial_number = appointment.patient.serial_number
        doctor_name = appointment.doctor.name

        subject = "Appointment Confirmed"

        values = {
            "email": patient_email,
            "name": patient_name,
            "username": patient_username,
            "serial_number": patient_serial_number,
            "doctor_name": doctor_name,
            "appointment_serial_num": appointment.serial_number,
            "appointment_date": appointment.date,
            "appointment_time": appointment.time,
            "appointment_status": appointment.appointment_status,
        }

        html_message = render_to_string('appointment_accept_mail.html', {'values': values})
        plain_message = strip_tags(html_message)

        try:
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None) or getattr(settings, 'EMAIL_HOST_USER', None)
            send_mail(subject, plain_message, from_email, [patient_email], html_message=html_message, fail_silently=False)
        except BadHeaderError:
            return HttpResponse('Invalid header found')
        except (smtplib.SMTPException, OSError) as exc:
            messages.warning(request, f'Appointment confirmed, but email could not be sent ({type(exc).__name__}).')
        
        
        messages.success(request, 'Appointment Confirmed')
        return redirect('patient-dashboard')

    context = {'patient': patient, 'doctor': doctor}
    return render(request, 'booking.html', context)

@csrf_exempt
@login_required(login_url="doctor-login")
def my_patients(request):
    if request.user.is_doctor:
        doctor = Doctor_Information.objects.get(user=request.user)
        appointments = Appointment.objects.filter(doctor=doctor).filter(appointment_status='confirmed')
        # patients = Patient.objects.all()
    else:
        redirect('doctor-logout')
    
    
    context = {'doctor': doctor, 'appointments': appointments}
    return render(request, 'my-patients.html', context)


# def patient_profile(request):
#     return render(request, 'patient_profile.html')

@csrf_exempt
@login_required(login_url="doctor-login")
def patient_profile(request, pk):
    if request.user.is_doctor:
        # doctor = Doctor_Information.objects.get(user_id=pk)
        doctor = Doctor_Information.objects.get(user=request.user)
        patient = Patient.objects.get(patient_id=pk)
        appointments = Appointment.objects.filter(doctor=doctor).filter(patient=patient)
        prescription = Prescription.objects.filter(doctor=doctor).filter(patient=patient)
        report = Report.objects.filter(doctor=doctor).filter(patient=patient) 
    else:
        redirect('doctor-logout')
    context = {'doctor': doctor, 'appointments': appointments, 'patient': patient, 'prescription': prescription, 'report': report}  
    return render(request, 'patient-profile.html', context)


@csrf_exempt
@login_required(login_url="doctor-login")
def create_prescription(request,pk):
        if request.user.is_doctor:
            doctor = Doctor_Information.objects.get(user=request.user)
            patient = Patient.objects.get(patient_id=pk) 
            create_date = datetime.date.today()

            appointment_id = request.GET.get('appointment_id') if request.method == 'GET' else request.POST.get('appointment_id')
            linked_appointment = None
            if appointment_id:
                try:
                    linked_appointment = Appointment.objects.get(id=int(appointment_id), doctor=doctor, patient=patient)
                except (ValueError, Appointment.DoesNotExist):
                    linked_appointment = None
            

            if request.method == 'POST':
                if appointment_id and linked_appointment is None:
                    messages.error(request, 'Invalid appointment for prescription.')
                    return redirect('appointments')

                if linked_appointment and Prescription.objects.filter(appointment=linked_appointment).exists():
                    messages.error(request, 'Prescription already exists for this appointment.')
                    return redirect('appointments')

                prescription = Prescription(doctor=doctor, patient=patient, appointment=linked_appointment)

                test_description = request.POST.getlist('description')
                medicine_name = request.POST.getlist('medicine_name')
                medicine_quantity = request.POST.getlist('quantity')
                medecine_frequency = request.POST.getlist('frequency')
                medicine_duration = request.POST.getlist('duration')
                medicine_relation_with_meal = request.POST.getlist('relation_with_meal')
                medicine_instruction = request.POST.getlist('instruction')
                extra_information = request.POST.get('extra_information')
                test_info_id = request.POST.getlist('id')

                def _redirect_back_with_appointment() -> HttpResponse:
                    url = reverse('create-prescription', kwargs={'pk': patient.patient_id})
                    if appointment_id:
                        url = f"{url}?appointment_id={appointment_id}"
                    return redirect(url)

                medicine_rows: list[dict[str, str]] = []
                max_medicine_len = max(
                    len(medicine_name),
                    len(medicine_quantity),
                    len(medecine_frequency),
                    len(medicine_relation_with_meal),
                    len(medicine_duration),
                    len(medicine_instruction),
                    0,
                )

                for index in range(max_medicine_len):
                    row = {
                        'medicine_name': (medicine_name[index] if index < len(medicine_name) else '').strip(),
                        'quantity': (medicine_quantity[index] if index < len(medicine_quantity) else '').strip(),
                        'frequency': (medecine_frequency[index] if index < len(medecine_frequency) else '').strip(),
                        'relation_with_meal': (medicine_relation_with_meal[index] if index < len(medicine_relation_with_meal) else '').strip(),
                        'duration': (medicine_duration[index] if index < len(medicine_duration) else '').strip(),
                        'instruction': (medicine_instruction[index] if index < len(medicine_instruction) else '').strip(),
                    }

                    if all(not value for value in row.values()):
                        continue

                    if any(not value for value in row.values()):
                        messages.error(request, 'All medicine fields are required. Please fill or remove empty medicine rows.')
                        return _redirect_back_with_appointment()

                    medicine_rows.append(row)

                resolved_tests: list[tuple[Test_Information, str]] = []
                max_test_len = max(len(test_info_id), len(test_description), 0)
                for index in range(max_test_len):
                    raw_test_id = (test_info_id[index] if index < len(test_info_id) else '')
                    raw_description = (test_description[index] if index < len(test_description) else '')

                    raw_test_id = str(raw_test_id).strip()
                    raw_description = str(raw_description).strip()

                    if not raw_test_id and not raw_description:
                        continue

                    if not raw_test_id or not raw_description:
                        messages.error(request, 'All test fields are required. Please fill or remove empty test rows.')
                        return _redirect_back_with_appointment()

                    try:
                        parsed_test_id = int(raw_test_id)
                    except ValueError:
                        messages.error(request, f'Invalid Test ID: {raw_test_id}')
                        return _redirect_back_with_appointment()

                    test_info = Test_Information.objects.filter(test_id=parsed_test_id).first()
                    if not test_info:
                        messages.error(request, f'Test ID {parsed_test_id} not found.')
                        return _redirect_back_with_appointment()

                    resolved_tests.append((test_info, raw_description))

            
                prescription.extra_information = extra_information
                prescription.create_date = create_date
                
                prescription.save()

                for row in medicine_rows:
                    medicine = Prescription_medicine(prescription=prescription)
                    medicine.medicine_name = row['medicine_name']
                    medicine.quantity = row['quantity']
                    medicine.frequency = row['frequency']
                    medicine.duration = row['duration']
                    medicine.instruction = row['instruction']
                    medicine.relation_with_meal = row['relation_with_meal']
                    medicine.save()

                for test_info, description_value in resolved_tests:
                    tests = Prescription_test(prescription=prescription)
                    tests.test_name = test_info.test_name
                    tests.test_description = description_value
                    tests.test_info_id = test_info.test_id
                    tests.test_info_price = test_info.test_price
                    tests.save()

                messages.success(request, 'Prescription Created')
                if linked_appointment:
                    return redirect('appointments')
                return redirect('patient-profile', pk=patient.patient_id)
             
            context = {'doctor': doctor, 'patient': patient, 'appointment': linked_appointment, 'appointment_id': appointment_id}  
        return render(request, 'create-prescription.html',context)

        
@csrf_exempt      
def render_to_pdf(template_src, context_dict={}):
    template=get_template(template_src)
    html=template.render(context_dict)
    result=BytesIO()
    pdf=pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(),content_type="aplication/pdf")
    return None

@csrf_exempt
def report_pdf(request, pk):
 if request.user.is_patient:
    patient = Patient.objects.get(user=request.user)
    report = Report.objects.get(report_id=pk)
    specimen = Specimen.objects.filter(report=report)
    test = Test.objects.filter(report=report)
    # current_date = datetime.date.today()
    context={'patient':patient,'report':report,'test':test,'specimen':specimen}
    pdf=render_to_pdf('report_pdf.html', context)
    if pdf:
        response=HttpResponse(pdf, content_type='application/pdf')
        content="inline; filename=report.pdf"
        # response['Content-Disposition']= content
        return response
    return HttpResponse("Not Found")


# def testing(request):
#     doctor = Doctor_Information.objects.get(user=request.user)
#     degree = doctor.degree
#     degree = re.sub("'", "", degree)
#     degree = degree.replace("[", "")
#     degree = degree.replace("]", "")
#     degree = degree.replace(",", "")
#     degree_array = degree.split()
    
#     education = zip(degree_array, institute_array)
    
#     context = {'doctor': doctor, 'degree': institute, 'institute_array': institute_array, 'education': education}
#     # test range, len, and loop to show variables before moving on to doctor profile
    
#     return render(request, 'testing.html', context)

@csrf_exempt
@login_required(login_url="login")
def patient_search(request, pk):
    if request.user.is_authenticated and request.user.is_doctor:
        doctor = Doctor_Information.objects.get(doctor_id=pk)
        id = int(request.GET['search_query'])
        patient = Patient.objects.get(patient_id=id)
        prescription = Prescription.objects.filter(doctor=doctor).filter(patient=patient)
        context = {'patient': patient, 'doctor': doctor, 'prescription': prescription}
        return render(request, 'patient-profile.html', context)
    else:
        logout(request)
        messages.info(request, 'Not Authorized')
        return render(request, 'doctor-login.html')

@csrf_exempt
@login_required(login_url="login")
def doctor_test_list(request):
    if request.user.is_authenticated and request.user.is_doctor:
        doctor = Doctor_Information.objects.get(user=request.user)
        tests = Test_Information.objects.all()
        context = {'doctor': doctor, 'tests': tests}
        return render(request, 'doctor-test-list.html', context)
    
    elif request.user.is_authenticated and request.user.is_patient:
        patient = Patient.objects.get(user=request.user)
        tests = Test_Information.objects.all()
        context = {'patient': patient, 'tests': tests}
        return render(request, 'doctor-test-list.html', context)
        
    else:
        logout(request)
        messages.info(request, 'Not Authorized')
        return render(request, 'doctor-login.html')


@csrf_exempt
@login_required(login_url="doctor-login")
def test_info_lookup(request):
    if not request.user.is_authenticated or not getattr(request.user, 'is_doctor', False):
        return JsonResponse({'found': False, 'error': 'Not authorized'}, status=403)

    raw_test_id = str(request.GET.get('test_id', '')).strip()
    if not raw_test_id:
        return JsonResponse({'found': False, 'error': 'Missing test_id'}, status=400)

    try:
        test_id = int(raw_test_id)
    except ValueError:
        return JsonResponse({'found': False, 'error': 'Invalid test_id'}, status=400)

    test_info = Test_Information.objects.filter(test_id=test_id).values('test_id', 'test_name', 'test_price').first()
    if not test_info:
        return JsonResponse({'found': False}, status=404)

    return JsonResponse({'found': True, **test_info})


@csrf_exempt
@login_required(login_url="login")
def doctor_view_prescription(request, pk):
    if request.user.is_authenticated and request.user.is_doctor:
        doctor = Doctor_Information.objects.get(user=request.user)
        prescriptions = Prescription.objects.get(prescription_id=pk)
        medicines = Prescription_medicine.objects.filter(prescription=prescriptions)
        tests = Prescription_test.objects.filter(prescription=prescriptions)
        context = {'prescription': prescriptions, 'medicines': medicines, 'tests': tests, 'doctor': doctor}
        return render(request, 'doctor-view-prescription.html', context)

@csrf_exempt
@login_required(login_url="login")
def doctor_view_report(request, pk):
    if request.user.is_authenticated and request.user.is_doctor:
        doctor = Doctor_Information.objects.get(user=request.user)
        report = Report.objects.get(report_id=pk)
        specimen = Specimen.objects.filter(report=report)
        test = Test.objects.filter(report=report)
        context = {'report': report, 'test': test, 'specimen': specimen, 'doctor': doctor}
        return render(request, 'doctor-view-report.html', context)
    else:
        logout(request)
        messages.info(request, 'Not Authorized')
        return render(request, 'doctor-login.html')


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

@csrf_exempt
@login_required(login_url="login")
def doctor_review(request, pk):
    if request.user.is_doctor:
        # doctor = Doctor_Information.objects.get(user_id=pk)
        doctor = Doctor_Information.objects.get(user=request.user)
            
        doctor_review = Doctor_review.objects.filter(doctor=doctor)
        
        context = {'doctor': doctor, 'doctor_review': doctor_review}  
        return render(request, 'doctor-profile.html', context)

    if request.user.is_patient:
        doctor = Doctor_Information.objects.get(doctor_id=pk)
        patient = Patient.objects.get(user=request.user)

        if request.method == 'POST':
            title = request.POST.get('title')
            message = request.POST.get('message')
            
            doctor_review = Doctor_review(doctor=doctor, patient=patient, title=title, message=message)
            doctor_review.save()

        context = {'doctor': doctor, 'patient': patient, 'doctor_review': doctor_review}  
        return render(request, 'doctor-profile.html', context)
    else:
        logout(request)
 
 
   
 



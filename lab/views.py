import logging
import os

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import cache_control
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q, Sum

from hospital.models import User
from hospital_admin.models import Clinical_Laboratory_Technician
from doctor.models import (
    Prescription, Prescription_test, Prescription_medicine,
    Doctor_Information,
)
from hospital.models import Patient
from sslcommerz.models import Payment

from .decorators import lab_login_required

logger = logging.getLogger(__name__)

# Allowed file extensions for report uploads
ALLOWED_REPORT_EXTENSIONS = {'.pdf', '.png', '.jpg', '.jpeg', '.docx', '.txt', '.doc'}
MAX_UPLOAD_SIZE_MB = 15


# -------------------------------------------------------------------
# Authentication
# -------------------------------------------------------------------

@csrf_exempt
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def lab_login(request):
    """Dedicated login page for Lab Technologists."""
    if request.user.is_authenticated and getattr(request.user, 'is_labworker', False):
        return redirect('lab-dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        if not username or not password:
            messages.error(request, 'Please enter both username and password.')
            return render(request, 'lab/login.html')

        try:
            User.objects.get(username=username)
        except User.DoesNotExist:
            messages.error(request, 'Username does not exist.')
            return render(request, 'lab/login.html')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.is_labworker:
                login(request, user)
                messages.success(request, 'Welcome to the Lab Dashboard!')
                return redirect('lab-dashboard')
            else:
                messages.error(request, 'This account is not registered as a Lab Technologist.')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'lab/login.html')


def lab_logout(request):
    logout(request)
    return redirect('lab-login')


# -------------------------------------------------------------------
# Dashboard
# -------------------------------------------------------------------

@lab_login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def lab_dashboard(request):
    """
    Main Lab Dashboard – shows ONLY tests from prescriptions where
    the test has been PAID (test_info_pay_status == 'Paid').
    """
    lab_worker = Clinical_Laboratory_Technician.objects.get(user=request.user)

    # Fetch only paid tests
    paid_tests = (
        Prescription_test.objects
        .filter(test_info_pay_status='Paid')
        .select_related('prescription', 'prescription__doctor', 'prescription__patient')
        .order_by('prescription__patient__patient_id', 'test_id')
    )

    # Apply filters from GET params
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('q', '')

    if status_filter and status_filter in ('Pending', 'Processing', 'Completed'):
        paid_tests = paid_tests.filter(test_status=status_filter)

    if search_query:
        paid_tests = paid_tests.filter(
            Q(test_name__icontains=search_query) |
            Q(prescription__patient__name__icontains=search_query) |
            Q(prescription__patient__username__icontains=search_query) |
            Q(prescription__doctor__name__icontains=search_query) |
            Q(prescription__prescription_id__icontains=search_query)
        )

    # Build enriched list with prescription-level data
    test_items = []
    for t in paid_tests:
        prescription = t.prescription
        # Get all paid tests for this prescription to calculate total paid
        sibling_tests = Prescription_test.objects.filter(
            prescription=prescription, test_info_pay_status='Paid'
        )
        total_paid = sum(float(st.test_info_price or 0) for st in sibling_tests)

        test_items.append({
            'test': t,
            'prescription': prescription,
            'patient': prescription.patient if prescription else None,
            'doctor': prescription.doctor if prescription else None,
            'total_paid': total_paid,
        })

    # Dashboard stat cards
    total_paid_count = Prescription_test.objects.filter(test_info_pay_status='Paid').count()
    pending_count = Prescription_test.objects.filter(test_info_pay_status='Paid', test_status='Pending').count()
    processing_count = Prescription_test.objects.filter(test_info_pay_status='Paid', test_status='Processing').count()
    completed_count = Prescription_test.objects.filter(test_info_pay_status='Paid', test_status='Completed').count()

    # Simple pagination (20 per page)
    page = int(request.GET.get('page', 1))
    per_page = 20
    total_items = len(test_items)
    total_pages = max(1, (total_items + per_page - 1) // per_page)
    page = max(1, min(page, total_pages))
    start = (page - 1) * per_page
    end = start + per_page
    page_items = test_items[start:end]
    page_range = range(1, total_pages + 1)

    context = {
        'lab_worker': lab_worker,
        'test_items': page_items,
        'total_paid_count': total_paid_count,
        'pending_count': pending_count,
        'processing_count': processing_count,
        'completed_count': completed_count,
        'current_page': page,
        'total_pages': total_pages,
        'page_range': page_range,
        'status_filter': status_filter,
        'search_query': search_query,
    }
    return render(request, 'lab/dashboard.html', context)


# -------------------------------------------------------------------
# Test Actions
# -------------------------------------------------------------------

@lab_login_required
def start_test(request, pk):
    """Change test status from Pending → Processing."""
    if request.method != 'POST':
        return redirect('lab-dashboard')
    test = get_object_or_404(Prescription_test, test_id=pk, test_info_pay_status='Paid')
    if test.test_status != 'Pending':
        messages.warning(request, 'This test is not in Pending status.')
        return redirect('lab-dashboard')

    test.test_status = 'Processing'
    test.assigned_lab_user = request.user
    test.save()
    messages.success(request, f'Test "{test.test_name}" is now Processing.')
    return redirect('lab-dashboard')


@lab_login_required
def complete_test(request, pk):
    """Change test status from Processing → Completed."""
    if request.method != 'POST':
        return redirect('lab-dashboard')
    test = get_object_or_404(Prescription_test, test_id=pk, test_info_pay_status='Paid')
    if test.test_status != 'Processing':
        messages.warning(request, 'This test is not in Processing status.')
        return redirect('lab-dashboard')

    # Validate that report file is uploaded before completing
    if not test.report_file:
        messages.error(request, 'Please upload report file before completing.')
        return redirect('lab-dashboard')

    test.test_status = 'Completed'
    test.completed_date = timezone.now()
    test.save()
    messages.success(request, f'Test "{test.test_name}" marked as Completed.')
    return redirect('lab-dashboard')


@lab_login_required
def upload_report(request, pk):
    """Upload a report file or text result for a test."""
    test = get_object_or_404(Prescription_test, test_id=pk, test_info_pay_status='Paid')

    if request.method != 'POST':
        return redirect('lab-dashboard')

    report_file = request.FILES.get('report_file')
    report_text = request.POST.get('report_text', '').strip()

    logger.info('Upload report for test_id=%s  file=%s  has_text=%s',
                pk, report_file, bool(report_text))

    if not report_file and not report_text:
        messages.error(request, 'Please provide a report file or text result.')
        return redirect('lab-dashboard')

    # Validate file type and size
    if report_file:
        ext = os.path.splitext(report_file.name)[1].lower()
        if ext not in ALLOWED_REPORT_EXTENSIONS:
            messages.error(
                request,
                f'Invalid file type "{ext}". Allowed: PDF, PNG, JPG, JPEG, DOCX, DOC, TXT.'
            )
            return redirect('lab-dashboard')

        if report_file.size > MAX_UPLOAD_SIZE_MB * 1024 * 1024:
            messages.error(
                request,
                f'File too large. Maximum allowed size is {MAX_UPLOAD_SIZE_MB} MB.'
            )
            return redirect('lab-dashboard')

        test.report_file = report_file

    if report_text:
        test.report_text = report_text

    # Auto-complete if still processing
    if test.test_status in ('Processing', 'Pending'):
        test.test_status = 'Completed'
        test.completed_date = timezone.now()

    test.assigned_lab_user = request.user
    test.save()
    messages.success(request, f'Report uploaded for "{test.test_name}".')
    return redirect('lab-dashboard')


@lab_login_required
def test_detail_api(request, pk):
    """Return JSON test detail for modal display."""
    test = get_object_or_404(Prescription_test, test_id=pk, test_info_pay_status='Paid')
    prescription = test.prescription

    # All tests in this prescription
    all_tests = Prescription_test.objects.filter(prescription=prescription)
    tests_list = []
    for t in all_tests:
        tests_list.append({
            'test_id': t.test_id,
            'test_name': t.test_name or '',
            'test_price': t.test_info_price or '0',
            'pay_status': t.test_info_pay_status or '',
            'test_status': t.test_status or 'Pending',
            'has_report': bool(t.report_file or t.report_text),
        })

    # All medicines in this prescription
    medicines = Prescription_medicine.objects.filter(prescription=prescription)
    meds_list = []
    for m in medicines:
        meds_list.append({
            'name': m.medicine_name or '',
            'quantity': m.quantity or '',
            'duration': m.duration or '',
            'frequency': m.frequency or '',
            'instruction': m.instruction or '',
        })

    patient = prescription.patient if prescription else None
    doctor = prescription.doctor if prescription else None

    data = {
        'test_id': test.test_id,
        'test_name': test.test_name or '',
        'test_description': test.test_description or '',
        'test_price': test.test_info_price or '0',
        'test_status': test.test_status or 'Pending',
        'pay_status': test.test_info_pay_status or '',
        'report_text': test.report_text or '',
        'report_file_url': test.report_file.url if test.report_file else '',
        'completed_date': str(test.completed_date) if test.completed_date else '',
        'prescription_id': prescription.prescription_id if prescription else '',
        'prescription_date': prescription.create_date or '' if prescription else '',
        'extra_info': prescription.extra_information or '' if prescription else '',
        'patient_name': patient.name or '' if patient else '',
        'patient_id': patient.patient_id if patient else '',
        'patient_phone': str(patient.phone_number or '') if patient else '',
        'patient_image': patient.featured_image.url if patient and patient.featured_image else '',
        'doctor_name': doctor.name or '' if doctor else '',
        'doctor_department': doctor.department or '' if doctor else '',
        'doctor_image': doctor.featured_image.url if doctor and doctor.featured_image else '',
        'all_tests': tests_list,
        'medicines': meds_list,
    }
    return JsonResponse(data)

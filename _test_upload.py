import os, django
os.environ['DJANGO_SETTINGS_MODULE'] = 'healthstack.settings'
django.setup()

from django.conf import settings
settings.ALLOWED_HOSTS = ['*']

from django.test import Client
from django.core.files.uploadedfile import SimpleUploadedFile
from hospital.models import User
from doctor.models import Prescription_test

user = User.objects.filter(is_labworker=True).first()
client = Client()
client.force_login(user)

# GET dashboard
resp = client.get('/lab/dashboard/')
html = resp.content.decode()

print('=== FORM CHECKS ===')
print('uploadReportForm:', 'uploadReportForm' in html)
print('enctype multipart:', 'multipart/form-data' in html)
print('csrfmiddlewaretoken:', 'csrfmiddlewaretoken' in html)
print('openUploadModal:', 'openUploadModal' in html)

print('\n=== MESSAGES JS (no messages) ===')
print('toast JS block:', 'new bootstrap.Toast' in html)

# Upload
test = Prescription_test.objects.filter(test_info_pay_status='Paid').first()
print('\nUsing test_id:', test.test_id, 'status:', test.test_status)

fake = SimpleUploadedFile('report.pdf', b'%PDF-1.4 test', content_type='application/pdf')
resp2 = client.post('/lab/upload-report/%s/' % test.test_id, {
    'report_file': fake,
    'report_text': 'Normal result',
}, follow=True)
html2 = resp2.content.decode()

print('\n=== AFTER UPLOAD (followed redirect) ===')
print('toast HTML rendered:', 'class="toast' in html2)
print('toast JS block present:', 'new bootstrap.Toast' in html2)
print('Success message text:', 'Report uploaded' in html2)

# Extract just the toast HTML
import re
toasts = re.findall(r'<div class="toast[^"]*"[^>]*>.*?</div>\s*</div>', html2, re.DOTALL)
for t in toasts:
    print('TOAST:', t[:200])

# Check the messages script block
script_block = re.findall(r'{% if messages %}.*?{% endif %}', html2, re.DOTALL)
if script_block:
    print('FOUND messages if-block:', script_block[0][:200])
else:
    print('NO {% if messages %} block found (already rendered as HTML)')

# Look for the actual script
if 'bootstrap.Toast' in html2:
    idx = html2.index('bootstrap.Toast')
    print('CONTEXT:', html2[max(0,idx-100):idx+100])
else:
    print('NO bootstrap.Toast JS found in rendered HTML')

"""Test the upload against the LIVE dev server on port 8000."""
import requests

BASE = 'http://127.0.0.1:8000'

s = requests.Session()

# 1. Get the lab login page to grab CSRF token
r = s.get(f'{BASE}/lab/')
print('Login page:', r.status_code)

# Extract CSRF token from the page
import re
csrf_match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', r.text)
if not csrf_match:
    print('ERROR: No CSRF token in login page')
    print('Page snippet:', r.text[:500])
    exit()
csrf_token = csrf_match.group(1)
print('CSRF token:', csrf_token[:20] + '...')

# 2. Login as a lab worker
r = s.post(f'{BASE}/lab/login/', data={
    'csrfmiddlewaretoken': csrf_token,
    'username': 'mamoni',
    'password': '1',
}, allow_redirects=False)
print('Login POST:', r.status_code, r.headers.get('Location', ''))

# Follow redirect
if r.status_code in (301, 302):
    r = s.get(BASE + r.headers['Location'])
    print('Dashboard after login:', r.status_code)

# 3. Get dashboard to get fresh CSRF token
r = s.get(f'{BASE}/lab/dashboard/')
print('Dashboard GET:', r.status_code)
csrf_match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', r.text)
if not csrf_match:
    print('ERROR: No CSRF token on dashboard')
    exit()
csrf_token2 = csrf_match.group(1)
print('Dashboard CSRF:', csrf_token2[:20] + '...')

# Check which tests have upload buttons
upload_buttons = re.findall(r'openUploadModal\((\d+),', r.text)
print('Tests with Upload button:', upload_buttons)

if not upload_buttons:
    print('NO upload buttons found!')
    # Show what tests appear
    test_ids = re.findall(r'openTestDetail\((\d+)\)', r.text)
    print('Tests on page:', test_ids)
    exit()

test_id = upload_buttons[0]
print(f'Will upload to test_id={test_id}')

# 4. Upload a report
import io
fake_file = io.BytesIO(b'%PDF-1.4 fake content')
fake_file.name = 'live_test_report.pdf'

r = s.post(f'{BASE}/lab/upload-report/{test_id}/', data={
    'csrfmiddlewaretoken': csrf_token2,
    'report_text': 'Live test result',
}, files={
    'report_file': ('live_test_report.pdf', fake_file, 'application/pdf'),
}, allow_redirects=False)

print(f'Upload POST: {r.status_code} Location: {r.headers.get("Location", "")}')

if r.status_code == 403:
    print('CSRF FAILURE! Response:', r.text[:300])
elif r.status_code in (301, 302):
    # Follow redirect to see messages
    r = s.get(BASE + r.headers['Location'])
    print('After redirect:', r.status_code)
    # Check for success toast
    if 'Report uploaded' in r.text:
        print('SUCCESS: Upload confirmed!')
    elif 'toast' in r.text:
        toasts = re.findall(r'toast-body">\s*(.*?)\s*</div>', r.text)
        print('Toast messages:', toasts)
    else:
        print('No toast messages found')
    # Check for View Report button for our test
    if f'lab-btn-view-report' in r.text:
        print('View Report button present')
else:
    print('Unexpected response:', r.status_code)
    print(r.text[:500])

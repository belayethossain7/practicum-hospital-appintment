import os, django
os.environ['DJANGO_SETTINGS_MODULE'] = 'healthstack.settings'
django.setup()
from django.conf import settings
settings.ALLOWED_HOSTS = ['*']

from django.test import Client
from hospital.models import User

u = User.objects.filter(is_labworker=True).first()
c = Client()
c.force_login(u)
r = c.get('/lab/dashboard/')
h = r.content.decode()

# Find action group HTML blocks 
import re
# Find from "lab-action-group" to the 4th closing </div> (since forms have nested divs)
blocks = re.findall(r'lab-action-group">(.*?)</div>\s*</td>', h, re.DOTALL)

for i, b in enumerate(blocks):
    print(f'=== ACTION BLOCK {i} ===')
    # Show key elements
    if 'openUploadModal' in b:
        print('  HAS Upload button')
    else:
        print('  NO Upload button')
    if 'lab-btn-view-report' in b:
        print('  HAS View Report button')
    else:
        print('  NO View Report button')
    if 'lab-start-test' in b:
        print('  HAS Start button')
    if 'lab-complete-test' in b:
        print('  HAS Complete button')
    if 'openTestDetail' in b:
        match = re.search(r'openTestDetail\((\d+)\)', b)
        print(f'  Test ID: {match.group(1)}')
    print()
    # Print trimmed content
    lines = [l.strip() for l in b.strip().split('\n') if l.strip()]
    for l in lines:
        print(f'  {l}')
    print()

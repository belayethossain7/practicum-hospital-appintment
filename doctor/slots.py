import datetime
import re
from typing import Iterable, List, Optional, Set

from django.db.models import QuerySet

from .models import Appointment, Doctor_Information


SLOT_START_HOUR = 10  # 10:00 AM
SLOT_END_HOUR = 16    # 4:00 PM (end-exclusive)
SLOT_INTERVAL_MINUTES = 30


def format_time_display(value: datetime.time) -> str:
    display = value.strftime('%I:%M %p')
    return display[1:] if display.startswith('0') else display


def parse_appointment_date(date_str: str) -> datetime.date:
    if not date_str:
        raise ValueError('Missing appointment date')

    date_str = str(date_str).strip()
    for fmt in ('%m/%d/%Y', '%Y-%m-%d'):
        try:
            return datetime.datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    raise ValueError('Invalid appointment date format')


def parse_appointment_time(time_str: str) -> datetime.time:
    if not time_str:
        raise ValueError('Missing appointment time')

    raw = str(time_str).strip()
    raw = re.sub(r'\s+', ' ', raw)

    raw_upper = raw.upper()
    raw_upper = raw_upper.replace('A.M.', 'AM').replace('P.M.', 'PM')

    candidates = [raw_upper, raw_upper.replace(' ', '')]
    for candidate in candidates:
        for fmt in ('%I:%M %p', '%I:%M%p', '%H:%M'):
            try:
                return datetime.datetime.strptime(candidate, fmt).time()
            except ValueError:
                continue

    raise ValueError('Invalid appointment time format')


def is_time_in_slot_window(value: datetime.time) -> bool:
    start = datetime.time(SLOT_START_HOUR, 0)
    end = datetime.time(SLOT_END_HOUR, 0)
    return start <= value < end


def is_valid_slot_increment(value: datetime.time) -> bool:
    return (value.minute % SLOT_INTERVAL_MINUTES) == 0 and value.second == 0 and value.microsecond == 0


def build_slot_labels() -> List[str]:
    labels: List[str] = []
    for hour in range(SLOT_START_HOUR, SLOT_END_HOUR):
        labels.append(format_time_display(datetime.time(hour, 0)))
        labels.append(format_time_display(datetime.time(hour, 30)))
    return labels


def get_doctor_booked_time_strings(doctor: Doctor_Information, date_value: datetime.date) -> Set[str]:
    booked = Appointment.objects.filter(
        doctor=doctor,
        date=date_value,
        appointment_status__in=['pending', 'confirmed'],
    ).values_list('time', flat=True)

    normalized: Set[str] = set()
    for t in booked:
        if not t:
            continue
        try:
            normalized.add(format_time_display(parse_appointment_time(t)))
        except ValueError:
            normalized.add(str(t).strip())
    return normalized


def get_available_slot_labels(
    doctor: Doctor_Information,
    date_value: datetime.date,
    *,
    now_local: Optional[datetime.datetime] = None,
) -> List[str]:
    """Return available slot labels for the doctor on the given date.

    Removes booked slots and (if date is today) removes slots that have already started.
    """
    if now_local is None:
        now_local = datetime.datetime.now()

    all_slots = build_slot_labels()
    booked = get_doctor_booked_time_strings(doctor, date_value)

    available: List[str] = []
    for label in all_slots:
        if label in booked:
            continue
        if date_value == now_local.date():
            try:
                slot_time = parse_appointment_time(label)
            except ValueError:
                slot_time = None
            if slot_time is not None and slot_time <= now_local.time():
                continue
        available.append(label)

    return available

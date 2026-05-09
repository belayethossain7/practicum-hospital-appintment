from django.db import migrations


def rename_square_hospital_variants(apps, schema_editor):
    """Rename all hospitals whose name starts with 'Square Hospital'
    to use 'Belayet Diagnostic Centre' branding."""
    Hospital_Information = apps.get_model('hospital', 'Hospital_Information')
    hospitals = Hospital_Information.objects.filter(name__icontains='Square Hospital')
    for hospital in hospitals:
        original = hospital.name or ''
        # Preserve any trailing suffix (e.g., " 1", " 2", " - Main Branch")
        suffix = original.replace('Square Hospital', '').strip()
        if suffix:
            new_name = f'Belayet Diagnostic Centre - {suffix}'
        else:
            new_name = 'Belayet Diagnostic Centre'
        hospital.name = new_name
        hospital.save()


def reverse_rename_variants(apps, schema_editor):
    """Reverse: rename Belayet Diagnostic Centre back to Square Hospital."""
    Hospital_Information = apps.get_model('hospital', 'Hospital_Information')
    hospitals = Hospital_Information.objects.filter(name__icontains='Belayet Diagnostic Centre')
    for hospital in hospitals:
        original = hospital.name or ''
        suffix = original.replace('Belayet Diagnostic Centre - ', '').replace('Belayet Diagnostic Centre', '').strip()
        if suffix:
            new_name = f'Square Hospital {suffix}'
        else:
            new_name = 'Square Hospital'
        hospital.name = new_name
        hospital.save()


class Migration(migrations.Migration):

    dependencies = [
        ('hospital', '0005_rename_square_hospital'),
    ]

    operations = [
        migrations.RunPython(rename_square_hospital_variants, reverse_code=reverse_rename_variants),
    ]
